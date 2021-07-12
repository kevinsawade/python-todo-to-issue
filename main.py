# -*- coding: utf-8 -*-
# python-todo-to-issue/main.py

# Copyright (c) 2021, Kevin Sawade (kevin.sawade@uni-konstanz.de)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
# * Neither the name of the copyright holders nor the names of any
#   contributors may be used to endorse or promote products derived
#   from this software without specific prior written permission.
#
# This file is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 2.1
# of the License, or (at your option) any later version.
#
# This file is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# Find the GNU Lesser General Public License under <http://www.gnu.org/licenses/>.
"""
Convert python Todos to github issues
=====================================

Preface
-------

This module converts todos from your project to issues on github. I took lots
of inspiration from Alastair Mooney's <a href="https://github.com/alstr/todo-to-issue-action">todo-to-issue-action</a>,
which is a much more complete library and allows more languages than just python.
However, it does not recognize google-style <a href="https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html#example-google">Todo labels</a>
, doesn't allow to skip todos (like doctest's skip) and has a proprietary diff
parser instead of using <a href="https://github.com/matiasb/python-unidiff">unidiff</a>.

Installation
------------

Use this action via github workflows.

What is regarded as a ToDo?
---------------------------

First of all: Only todos from commits are used as issues. If you have old Todos
in your module, you need to remove them, commit and then include them again.

Todos are searched for in comments which start with ``# Todo:``. You can expand
these comments with the assignee of the issue. For this you put the github
username of a maintainer, developer or owner of a repo in parentheses. You can
also write multi-line todos, by indenting them with extra spaces. Using this
multi-line syntax, you can add labels and milestone to a issue.

```python
# todo: This is a simple in-line todo. This will be the title of the issue.

# todo (kevinsawade): I will fix this weird contraption.

# Todo: This is the title of a mutli-line issue.
#  This is the body of the multi-line issue. Here, you can specify
#  What needs to be done to fix this issue. Issues are automatically
#  closed, once the issue is removed from the file. You can set assignees,
#  labels and milestone like so:
#  assignees: kevinsawade, github_user3
#  labels: devel, bug
#  milestone: release
```

Besides these in-line Todos, Todos from google-style formatted docstrings will
also be picked up. The general style is the same. Indentation is done via
4 spaces. Assignees can be put in parentheses or as a line in multi-line todos.

```python
def myfunc(arg1):
\"\"\"This is the overview docstring.

This is more detailed info to the function `myfunc`.

Args:
    arg1 (str): Argument `arg1` should be of type `str`.

Todo:
    * Single-line todos are introduced as a single bullet-point.
    * This line becomes the title of the github issue.
    * (kevinsawade) Assignees are put into parentheses.
    * Titles for multi-line todos are also bullet-points.
        But the body is indented according to google's styleguide.
        Assignees, labels and milestones are added similar to the in-line
        comments todos.
        assignees: kevinsawade, github_user2
        labels: devel, bug
        milestone: alpha

\"\"\"
return 'Hello!' + arg1
```

To skip todos you can add ``# todo: +SKIP`` after the todo-line. This one is not
case insensitive and only works if you use it verbose.

Classes and Functions
---------------------

The remainder of this page contains the functions and classes used to run this
action. These functions and classes contain their own documentation which you
can use if you only want to use some parts of this code.



"""
################################################################################
# Globals
################################################################################


# __all__ = ['main', 'GitHubClient']


################################################################################
# Regex Patterns
################################################################################


TODO_CHARS_PATTERN = '[*#]'
# Thanks to Alastair Mooney's regexes

INLINE_TODO_PATTERN = r'\s*#\s(?i)todo(\:|\s)(\s|\().*'
DOCSTRING_TODO_PATTERN = r'\s*\*\s*(\(.*|.*)'
TODO_SKIP_SUBSTRING = '# todo: +SKIP'


################################################################################
# Imports
################################################################################


from enum import Enum
import ast, os, requests, json, git, re, unittest
from unidiff import PatchSet
from io import StringIO


################################################################################
# Functions
################################################################################


def join_lines(issue, line_break):
    """Joins lines using a defined line_break.

    Args:
        issue (Issue): An `Issue` instance.
        line_break (str): The line-break used in `GitHubClient`.

    Returns:
        str: A string with the formatted issue body.

    """
    annotation = "This issue was automatically created by a github action that converts project Todos to issues."
    return annotation + '\n\n' + line_break.join(issue.body)


def get_body(issue, url, line_break):
    """Constructs a body with issue and url.

    Args:
        issue (Issue): An `Issue` instance.
        url (str): The url constructed from `GitHubClient`.
        line_break (str): The line-break used in `GitHubClient`.

    Returns:
        str: A string with the body of the issue.

    """
    formatted_issue_body = join_lines(issue, line_break)
    formatted = (formatted_issue_body + '\n\n'
                 + url + '\n\n'
                 + '```' + issue.markdown_language + '\n'
                 + issue.hunk + '\n'
                 + '```')
    return formatted


def _get_assignees(lines):
    assignees = []
    if len(lines) > 1:
        for i, line in enumerate(lines):
            if line.lstrip().startswith('assignees:'):
                lines.pop(i)
                line = line.lstrip().lstrip('assignees:')
                assignees = [elem.strip() for elem in line.strip().split(',')]
        return lines, assignees
    elif len(lines) == 1:
        if '(' in lines[0]:
            s = lines[0]
            assignees = s[s.find("(") + 1:s.find(")")]
            lines[0] = lines[0].replace('(' + assignees + ')', '')
            assignees = [elem.strip() for elem in assignees.strip().split(',')]
        return lines, assignees


def _get_labels(lines):
    labels = []
    for i, line in enumerate(lines):
        if line.lstrip().startswith('labels:'):
            lines.pop(i)
            line = line.lstrip().lstrip('labels:')
            labels = [elem.strip() for elem in line.strip().split(',')]
    return lines, labels


def _get_milestone(lines):
    milestone = None
    for i, line in enumerate(lines):
        if line.lstrip().startswith(('milestone:', 'milestones:')):
            lines.pop(i)
            if 'milestone:' in line:
                milestone = line.lstrip().lstrip('milestone:').strip()
            elif 'milestones:' in line:
                milestone = line.lstrip().lstrip('milestones:').strip()
    return lines, milestone


################################################################################
# Classes
################################################################################

class LineStatus(Enum):
    """Represents the status of a line in a diff file."""
    ADDED = 0
    DELETED = 1
    UNCHANGED = 2


testing_values = dict(
    title='TEST AUTO ISSUE',
    labels=['todo'],
    assignees=[],
    milestone=None,
    body=[
        'This issue is automatically created by Unittests. If this issue is not automatically closed, tests have failed.'],
    hunk="# This is the code block that would normally be attached to the issue.\ndef function()\n    return 'Hi!'",
    file_name='main.py',
    start_line='47',
    markdown_language='python',
    status=LineStatus.ADDED
)


class Issue:
    """Issue class, filled with attributes to create issues from.

    Attributes:
        title (str): The title of the issue.
        labels (list[str]): Labels, that should be added to the issue. Default
            labels contains the 'todo' label.
        assignees (list[str]): Can be []. Assignees need to be maintainer
            of the repository.
        milestone (Union[str, None]): Can be None. Milestone needs to be one of
            the already defined milestones in the repo.
        body (list[str]): The lines of the issue body. The issue body will
            automatically appended with a useful url and a markdown code block
            defined in `hunk`.
        hunk (str): Newline separated string of code, that produced the todo.
        file_name (str): Name of the file that produced the todo. If file is
            somewhere, the path starting from repo root needs te be included.
        start_line (str): The line where the todo comment starts.
        markdown_language (str): The language of `hunk`.
        status (LineStatus): An instance of the `LineStatus` Enum class.

    """

    def __init__(self, testing=0, **kwargs):
        if testing:
            for key, val in testing_values.items():
                self.__setattr__(key, val)
            return

        for key, val in kwargs.items():
            self.__setattr__(key, val)
        for key in testing_values.keys():
            try:
                self.__getattribute__(key)
            except AttributeError:
                raise TypeError(f'__init__() missing 1 required argument: {key}')
        if 'todo' not in self.labels:
            self.labels.append('todo')

    def __str__(self):
        string = f"Title: {self.title}, assignees: [{', '.join(self.assignees)}], milestone: {self.milestone}, status: {self.status}]\n"
        return string

    def __repr__(self):
        return self.__str__()


class GitHubClient():
    """Class to interact with GitHub, read and create issues.

    This class interacts with GitHub via api.github.com and reads issues from
    repositories. The default behavior is, that it uses git-python to get the
    url of the current remote origin. This name of the repo is usually built
    like this: user_name/repo_name or org_name/repo_name. git-python is also
    used to get the sha of the current commit and the previous commit.

    About tokens: To work with private repos and to have the ability to close
    issues in a repository, this class needs github token, sometimes also called
    a secret. The secret can be created in your github account. Visit
    https://github.com/settings/tokens and click 'Generate a new token'. Check
    the 'repo' scope and give the token a descriptive name. If the repo lies
    within an organisation, the token of a user with access rights to the org
    repo, will suffice.

    About secrets: This token should not fall into the wrong hands. However, in
    production and in testing the token is needed. In production, the token can
    be provided as a secret. Add the token as a secret in the settings page of
    your repo. In testing, the token is provided by placing a file called
    'secrets' in the repo's root directory.

    Attributes:
        existing_issues (list): A list of existing issues.
        testing (bool): Used, when this class is used in testing. Changes some
            behaviors.
        repo (str): A string of 'user_name/repo_name' or 'org_name/repo_name'
            which identifies the repo on github.com.
        sha (str): The 7 character sha hash of the current commit.
        before (str): The 7 character sha hash of the previous commit.
        token (str): A github token.
        base_url (str): A string containing 'https://api.github.com/'.
        repos_url (str): base_url + 'repos/'
        issues_url (str): GitHub API url pointing to a url with the current
            repo's issues.
        issue_headers (dict): A dict to provide to requests.get() as header.

    """

    def __init__(self, testing=0):
        """Instantiate the GitHubClient.

        Keyword Args:
            testing (bool, optional): Whether class is used during testing.

        """
        # set some attributes right from the start
        self.existing_issues = []
        self.testing = testing

        # get repo using git-python
        repo = git.Repo('.')
        remote_url = repo.remotes[0].config_reader.get("url")
        self.repo = remote_url.lstrip('https://github.com/').rstrip('.git')

        # get before and current hash
        commits = [i for i in repo.iter_commits()]
        self.sha = repo.git.rev_parse(commits[0].hexsha, short=True)
        self.before = repo.git.rev_parse(commits[1].hexsha, short=True)
        if self.testing == 1:
            self.sha = '036ef2ca'
            self.before = '11858e41'
        elif self.testing == 2:
            self.sha = '7fae83cc'
            self.before = '036ef2ca'

        # get the token from environment variables
        self.token = os.getenv('INPUT_TOKEN')

        # define line break. Can also be \n\n which formats multi-line todos
        # nicer.
        self.line_break = '\n'

        # set other attributes
        self.base_url = 'https://api.github.com/'
        self.repos_url = f'{self.base_url}repos/'
        self.issues_url = f'{self.repos_url}{self.repo}/issues'
        self.issue_headers = {
            'Content-Type': 'application/json',
            'Authorization': f'token {self.token}'
        }

        # get current issues
        self._get_existing_issues()

    def _get_existing_issues(self, page=1):
        """Populate the existing issues list."""
        params = {
            'per_page': 100,
            'page': page,
            'state': 'open',
            'labels': 'todo'
        }
        list_issues_request = requests.get(self.issues_url, headers=self.issue_headers, params=params)
        if list_issues_request.status_code == 200:
            # check
            self.existing_issues.extend(list_issues_request.json())
            links = list_issues_request.links
            if 'next' in links:
                self._get_existing_issues(page + 1)

    @staticmethod
    def is_same_issue(issue, other_issue, line_break):
        """Compares two issues.

        Args:
            issue (Issue): Instance of `Issue`.
            other_issue (dict): Json dict returned from GitHub API of another issue.
            url_to_line (str): The url built by the `GitHubClient`.
            line_break (str): The line-break used in `GitHubClient`.

        Returns
            bool: Whether issues are identical or not.

        """
        # check title
        a = issue.title == other_issue['title']
        if not 'https://github.com/' in other_issue['body']:
            return a
        else:
            # check issue text
            this_text = join_lines(issue, line_break).rstrip()
            other_text = other_issue['body'].split('https://github.com')[0].rstrip()
            b = this_text == other_text

        return a and b

    def create_issue(self, issue):
        """Creates issue on github from an Issue class.

        Keyword Args:
            issue (Issue): An instance of the `Issue` class in this document.

        """
        # truncate issue title if too long
        title = issue.title
        if len(title) > 80:
            title = tile[:80] + '...'

        # define url to line
        url_to_line = f'https://github.com/{self.repo}/blob/{self.sha}/{issue.file_name}#L{issue.start_line}'

        # construct the issue body
        body = get_body(issue, url_to_line, self.line_break)

        # Alastair Mooney's has problems with rebasing. Let's see how this works out
        # One could use GitHub's GraphQL API
        for existing_issue in self.existing_issues:
            if self.__class__.is_same_issue(issue, existing_issue, self.line_break):
                # The issue_id matching means the issue issues are identical.
                print(f'Skipping issue (already exists)')
                return

        new_issue_body = {'title': title, 'body': body, 'labels': issue.labels}

        # check whether milestones are existent
        if issue.milestone:
            milestone_url = f'{self.repos_url}{self.repo}/milestones/{issue.milestone}'
            milestone_request = requests.get(url=milestone_url, headers=self.issue_headers)
            if milestone_request.status_code == 200:
                new_issue_body['milestone'] = issue.milestone
            else:
                print(f'Milestone {issue.milestone} does not exist! Dropping this parameter!')

        # check whether label exists
        valid_assignees = []
        for assignee in issue.assignees:
            assignee_url = f'{self.repos_url}{self.repo}/assignees/{assignee}'
            assignee_request = requests.get(url=assignee_url, headers=self.issue_headers)
            if assignee_request.status_code == 204:
                valid_assignees.append(assignee)
            else:
                print(f'Assignee {assignee} does not exist! Dropping this assignee!')
        new_issue_body['assignees'] = valid_assignees

        new_issue_request = requests.post(url=self.issues_url, headers=self.issue_headers,
                                          data=json.dumps(new_issue_body))

        return new_issue_request

    def close_issue(self, issue):
        """Check to see if this issue can be found on GitHub and if so close it.
        
        Keyword Args:
            issue (Issue): An instance of the `Issue` class in this document.
            
        """
        matched = 0
        issue_number = None
        for existing_issue in self.existing_issues:
            # This is admittedly a simple check that may not work in complex scenarios, but we can't deal with them yet.
            if self.__class__.is_same_issue(issue, existing_issue, self.line_break):
                print("matched")
                matched += 1
                # If there are multiple issues with similar titles, don't try and close any.
                if matched > 1:
                    print(f'Skipping issue (multiple matches)')
                    break
                issue_number = existing_issue['number']
        else:
            if matched == 0 and self.testing:
                raise Exception(f"Couldn't match issue {issue.title}, {issue.body}")
            else:
                # The titles match, so we will try and close the issue.
                update_issue_url = f'{self.repos_url}{self.repo}/issues/{issue_number}'
                body = {'state': 'closed'}
                close_issue_request = requests.patch(update_issue_url, headers=self.issue_headers, data=json.dumps(body))

                issue_comment_url = f'{self.repos_url}{self.repo}/issues/{issue_number}/comments'
                body = {'body': f'Closed in {self.sha}'}
                update_issue_request = requests.post(issue_comment_url, headers=self.issue_headers,
                                                     data=json.dumps(body))
                return update_issue_request.status_code, close_issue_request.status_code
        return None


class ToDo:
    """Class that parses google-style docstring todos from git diff hunks.

    Attributes:
        line (unidiff.Line): The line that triggered this todo.
        block (list[str]): The lines following the title of multi-line
            todos. Every line is one string in this list of str.
        status (LineStatus): The status of the ToDo. Can be ADDED or DELETED>
        markdown_language (str): What markdown language to use. Defaults to
            'python'.
        hunk (unidiff.Hunk): The hunk that contains the line. Will be converted
            to code block in the issue.
        file_name (str): The path of the file from which the todo was extracted.
        target_line (Union[str, int]): The line number from which the
            todo was raised. Is used to create a permalink url to that line.
        assignees (list[str]): The assignees of the issue.
        labels (list[str]): The labels of the issue.
        milestone (Union[None, str]): The milestone of the issue.
        title (str): The title of the issue, once the block input
            argument has been parsed.
        body (Union[str, list[str]]): The body of the issue. Can be empty string
            (no body_, or list of str for every line in body.

    """

    def __init__(self, line, block, hunk, file):
        """Instantiate the ToDo Class.

        Args:
            line (unidiff.Line): The line from which the todo was raised.
            block (str): The complete indented block, the ToDo was raised from.
                Including the title.
            hunk (unidiff.Hunk): The hunk of diff from wich the todo was triggered.
            file (unidiff.File): The file, from which the diff was
                extracted.

        """
        self.line = line

        if line.is_added:
            self.status = LineStatus.ADDED
        else:
            self.status = LineStatus.DELETED

        self.block = block.strip()
        self.markdown_language = 'python'
        self.hunk = ''.join([l.value for l in hunk.target_lines()])
        if self.hunk.count('"""') == 1:
            if '"""' in self.hunk[:int(len(self.hunk) / 2)]:
                self.hunk = self.hunk + '"""\n'
            else:
                self.hunk = '"""\n' + self.hunk
        self.file_name = file.target_file.lstrip('b/')
        self.target_line = line.target_line_no

        # parse the block
        self._parse_block()

    def _parse_block(self):
        """Parses the `block` argument and extacts more info."""
        lines = self.block.split('\n')
        lines, self.assignees = _get_assignees(lines)
        lines, self.labels = _get_labels(lines)
        lines, self.milestone = _get_milestone(lines)
        if len(lines) > 1:
            self.title, self.body = lines[0].lstrip(), '\n'.join(lines[1:])
            self.body = [line.lstrip() for line in self.body.splitlines()]
        else:
            self.title = lines[0].lstrip()
            self.body = ""

    @property
    def issue(self):
        issue = Issue(
            title=self.title,
            labels=['todo'] + self.labels,
            assignees=self.assignees,
            milestone=self.milestone,
            body=self.body,
            hunk=self.hunk,
            file_name=self.file_name,
            start_line=self.target_line,
            markdown_language=self.markdown_language,
            status=self.status
        )
        return issue

    def __bool__(self):
        return True


class TodoParser:
    """Class that parses git diffs and looks for todo strings.

    First things first, the Todos can be skipped with a syntax similar to doctest.
    Adding a comment with # todo: +SKIP to the line skips the todo. The example
    todos which follow now all contain this SKIP command, because we don't want
    this class to raise issues in the explanatory section. Here are examples of
    how to put todos that will be picked up by this parser:

    Examples:
        A single commented line starting with todo (case insensitive).::

            # todo: This needs to be looked into. # todo: +SKIP

        Using parentheses, you can assign people to todos. If these people are
        part of the github repo, they will be assigned to the issue, that is
        raised from this todo. Please use their github username::

            # todo (tensorflower-gardener): Tensorflow's bot should fix this. # todo: +SKIP

        With extended syntax you can add existing labels and exisitng milestones
        to your todos.::

            # todo: This is the title of the todo. # todo: +SKIP
            #  Further text is indented by a single space. It will appear
            #  In the body of the issue. You can add assignees, and labels
            #  with this syntax. The `todo` label will automatically
            #  added to your labels.
            #  assignees: github_user, kevinsawade, another_user
            #  labels: devel, urgent
            #  milestones: alpha

        Besides these in-comment todos, this class also scans for google-style
        todo's in python docstrings.::

            def myfunc(arg1):
                '''This is a docstring.

                Args:
                    arg1: A thing.

                Todo:
                    * Single-line Todo. Add more documentation. # todo: +SKIP
                    * (kevinsawade) We should also add some actual code. # todo: +SKIP
                    * Multi-line todos should follow google-styleguide. # todo: +SKIP
                        This means a tab should be used indentation inside
                        the docstrings. This will form the body of the issue.
                        Assignees and labels can be added the same way:
                        assignees: github_user2, user3
                        labels: wontfix, devel
                        milestones: alpha

                '''

    Attributes:
        issues (list[Issue]): A list of Issue instances.
        testing (bool): Whether testing is carried out.
        repo (str): A url to the current repo.

    """

    def __init__(self, testing=0):
        """Instantiate the TodoParser class.

        Keyword Args:
            testing (bool, optional): Whether testing is carried out with this
                class. Defaults to False.

        """
        self.testing = testing
        self.issues = []
        self._parse()

    def _parse(self):
        """Parse the diffs and search for todos in added lines."""
        repo = git.Repo('.')
        remote_url = repo.remotes[0].config_reader.get("url")
        self.repo = remote_url.lstrip('https://github.com/').rstrip('.git')

        # get before and current hash
        commits = [i for i in repo.iter_commits()]
        self.sha = repo.git.rev_parse(commits[0].hexsha, short=True)
        self.before = repo.git.rev_parse(commits[1].hexsha, short=True)
        if self.testing == 1:
            self.sha = '036ef2ca'
            self.before = '11858e41'
        elif self.testing == 2:
            self.sha = '7fae83cc'
            self.before = '036ef2ca'
        commit_now = repo.commit(self.sha)
        commit_before = repo.commit(self.before)

        # get diff
        self.diff = repo.git.diff(self.before, self.sha)
        patchset = PatchSet(self.diff)

        for file in patchset:
            file_before = file.source_file.lstrip('a/')
            file_before = StringIO(commit_before.tree[file_before].data_stream.read().decode('utf-8'))
            file_after = file.target_file.lstrip('b/')
            file_after = StringIO(commit_now.tree[file_after].data_stream.read().decode('utf-8'))
            with file_before as f:
                todos_before = extract_todos_from_file(f.read(), self.testing)
            with file_after as f:
                todos_now = extract_todos_from_file(f.read(), self.testing)
            for hunk in file:
                lines = list(hunk.source_lines()) + list(hunk.target_lines())
                for i, line in enumerate(lines):
                    if block := is_todo_line(line, todos_before, todos_now, self.testing):
                        todo = ToDo(line, block, hunk, file)
                        issue = todo.issue
                        self.issues.append(issue)


def is_todo_line(line, todos_before, todos_now, testing=0):
    """Two cases: Line starts with any combination of # Todo, or line starts with
    asterisk and is inside a napoleon docstring todo header.

    Also filter out # todo: +SKIP.

    Args:
        line (unidiff.Line): A line instance.
        todos_before (list[str]): Todos from the source file.
        todos_now (list[str]): Todos from the target file.

    Keyword Args:
        testing (bool, optional): Set True for Testing. Defaults to False.

    Returns:
        Union[bool, str]: Either a bool, when line is not a todo line, or a
            str, when line is a todo line.

    """
    if testing == 2 and line.value == 'I will add many.':
        print(line)
        raise Exception("STOP")
    # check if line has been added or removed
    if line.is_context:
        return False
    elif line.is_added:
        todos = todos_now
    else:
        todos = todos_before

    # check whether line can be a todo line
    if re.match(INLINE_TODO_PATTERN, line.value, re.MULTILINE) and not TODO_SKIP_SUBSTRING in line.value:
        stripped_line = strip_line(line.value.replace('#', '', 1))
    elif re.match(DOCSTRING_TODO_PATTERN, line.value, re.MULTILINE) and not TODO_SKIP_SUBSTRING in line.value:
        stripped_line = strip_line(line.value.replace('*', '', 1))
    else:
        return False

    # get the complete block
    # and build complete issue
    check = [stripped_line in t for t in todos]
    if any(check):
        index = check.index(True)
        block = todos[index]
        return block
    else:
        return False


def extract_todos_from_file(file, testing=0):
    """Parses a file and extracts todos in google-style formatted docstrings.

    Args:
        file (str): Contents of file.

    Keyword Args:
        testing (bool, optional): If set to True todos containing `# todo: +SKIP`
            will be disregarded. Defaults to False.

    Returns:
        list[str]: A list containing the todos from this file.

    """

    # use ast to parse
    docs = []
    parsed_file = ast.parse(file)
    try:
        docs.append(ast.get_docstring(parsed_file))
    except Exception as e:
        raise Exception("Exclude this specific exception") from e
    for node in parsed_file.body:
        try:
            docs.append(ast.get_docstring(node))
        except TypeError:
            pass

    # append docstring todos to list:
    todos = []
    for doc in docs:
        if doc is None:
            continue
        blocks = doc.split('\n\n')
        for block in blocks:
            if 'Todo:' in block:
                block = '\n'.join(block.splitlines()[1:])
                block = block.split('* ')[1:]
                if not testing:
                    block = list(filter(lambda x: False if TODO_SKIP_SUBSTRING in x else True, block))
                block = list(map(strip_line, block))
                block = list(map(lambda x: x.replace('\n ', '\n'), block))
                todos.extend(block)

    # get all comments lines starting with hash
    comments_lines = list(
        map(
            lambda x: x.strip().replace('#', '', 1),
            filter(
                lambda y: True if y.strip().startswith('#') else False,
                file.splitlines())))

    # iterate over them.
    for i, comment_line in enumerate(comments_lines):
        if comment_line.lower().strip().startswith('todo'):
            if not testing and TODO_SKIP_SUBSTRING in comment_line:
                continue
            block = [strip_line(comment_line)]
            in_block = True
            j = i + 1
            while in_block:
                try:
                    todo_body = comments_lines[j].startswith('  ')
                except IndexError:
                    in_block = False
                    continue
                if todo_body:
                    block.append(strip_line(comments_lines[j]))
                    j += 1
                else:
                    in_block = False
            block = '\n'.join(block)
            todos.append(block)

    # and return
    return todos


def strip_line(line, with_whitespace=True, with_todo=True):
    """Strips line from unwanted whitespace. comments chars, and 'todo'.

    Args:
        line (str): The line to be stripped.

    Keyword Args:
        with_whitespace (bool, optional): Whether to strip the whitespace
            that follows the comment character '#'.
            Defaults to True.
        with_todo (bool, optional): Whether to replace case insensitive
            'todo' strings.

    Returns:
        str: The stripped line.

    """
    if with_whitespace:
        line = line.strip().lstrip('#').lstrip()
    else:
        line = line.strip().lstrip('#')
    if with_todo:
        return re.sub(r'(?i)todo(\s|\:)', '', line).strip()
    else:
        return line


################################################################################
# Main
################################################################################


def run_tests_from_main():
    """Runs unit-tests when `main()` is called with testing = True."""
    # load a file with secrets if there
    try:
        with open('secrets', 'r') as f:
            gh_token = f.readline()
        os.environ['INPUT_TOKEN'] = gh_token
    except FileNotFoundError:
        pass

    # run unittests
    loader = unittest.TestLoader()
    test_suite = loader.discover(start_dir=os.path.join(os.getcwd(), 'tests'),
                                 top_level_dir=os.getcwd())
    runner = unittest.TextTestRunner()
    result = runner.run(test_suite)
    
    return result


def main(testing):
    if testing or os.getenv('INPUT_TESTING') == 'true':
        if not os.path.isfile('tests/test_todo_to_issue.py'):
            raise Exception("Please switch the TESTING argument in your workflow.yml file to 'false'. Tests will only run in the python-todo-to-issue repository.")
        result = run_tests_from_main()
        if not result.wasSuccessful():
            print("Tests were not successful. Exiting.")
            exit(1)
        else:
            print("Tests were successful")
    else:
        print("Running python-todo-to-issue")
        from pprint import pprint
        pprint(os.environ)
        print('\n')
        print(os.getenv('INPUT_TOKEN'))
        client = GitHubClient()
        issues = client.existing_issues
        pprint(issues)
        print("Exiting")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Python code Todos to github issues.")
    parser.add_argument('--testing', dest='testing', action='store_true',
                        help="Whether a testing run is executed and tests will be conducted.")
    parser.set_defaults(testing=False)
    args = parser.parse_args()
    main(testing=args.testing)
