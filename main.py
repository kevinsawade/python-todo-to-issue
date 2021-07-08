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
"""Convert python Todos to github issues.

"""
################################################################################
# Globals
################################################################################


__all__ = ['main', 'GitHubClient']


################################################################################
# Regex Patterns
################################################################################


TODO_CHARS_PATTERN = '[*#]'
# Thanks to Alastair Mooney's regexes
LABELS_PATTERN = r'(?<=labels:\s).+'
ASSIGNEES_PATTERN = r'(?<=assignees:\s).+'
MILESTONE_PATTERN = r'(?<=milestone:\s).+'

INLINE_TODO_PATTERN = r'\s*#\s(?i)todo(\:|\s)(\s|\().*'
DOCSTRING_TODO_PATTERN = r'\s*\*\s*(\(.*|.*)'
TODO_SKIP_SUBSTRING = '# todo: +SKIP'


################################################################################
# Imports
################################################################################

from enum import Enum
import ast, os, requests, json, git, re
from sphinxcontrib.napoleon import GoogleDocstring
from sphinxcontrib.napoleon import Config
napoleon_config = Config(napoleon_use_param=True, napoleon_use_rtype=True)
from unidiff import PatchSet

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
    return "This issue was automatically created by a github action that converts projects Todos to issues." + '\n\n' + line_break.join(issue.body)


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
    return (formatted_issue_body + '\n\n'
            + url + '\n\n'
            + '```' + issue.markdown_language + '\n'
            + issue.hunk + '\n'
            + '```')


def _get_assignees(lines):
    for i, line in enumerate(lines):
        if line.startswith('assignees:'):
            lines.pop(i)
            line = line.lstrip('assignees:')
            assignees = [elem.strip() for elem in line.strip().split(',')]
    return lines, assignees


def _get_labels(lines):
    for i, line in enumerate(lines):
        if line.startswith('labels:'):
            lines.pop(i)
            line = line.lstrip('labels:')
            labels = [elem.strip() for elem in line.strip().split(',')]
    return lines, labels


def _get_milestone(lines):
    for i, line in enumerate(lines):
        if line.startswith('milestone:'):
            lines.pop(i)
            line = line.lstrip('milestone:').strip()
    return lines, line

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
    body=['This issue is automatically created by Unittests. If this issue is not automatically closed, tests have failed.'],
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
    def __init__(self, testing=False, **kwargs):
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
        return self.title + ' ' + ' '.join(self.assignees) + ' ' + str(self.status)

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
    def __init__(self, testing=False):
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
            return False
        else:
            # check issue text
            this_text = join_lines(issue, line_break)
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
            # The titles match, so we will try and close the issue.
            update_issue_url = f'{self.repos_url}{self.repo}/issues/{issue_number}'
            body = {'state': 'closed'}
            requests.patch(update_issue_url, headers=self.issue_headers, data=json.dumps(body))

            issue_comment_url = f'{self.repos_url}{self.repo}/issues/{issue_number}/comments'
            body = {'body': f'Closed in {self.sha}'}
            update_issue_request = requests.post(issue_comment_url, headers=self.issue_headers,
                                                 data=json.dumps(body))
            return update_issue_request.status_code
        return None


class InlineTodo:
    """Class that parses in-line todos from git diff hunks."""
    def __init__(self):
        pass

    def __bool__(self):
        return True


class DocstringTodo:
    """Class that parses google-style docstring todos from git diff hunks."""
    def __init__(self):
        pass

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
    def __init__(self, testing=False):
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

        if self.testing:
            import glob
            diff_files = glob.glob('tests/*diff*.txt')
            for i, file in enumerate(diff_files):
                if i == 0:
                    patchset = PatchSet.from_filename(file)
                else:
                    patchset.extend(PatchSet.from_filename(file))
        else:
            diff = repo.git.diff(self.before, self.sha)
            patchset = PatchSet(diff)

        for file in patchset:
            todos_before
            todos_now = extract_todos_from_file(file.target_file, self.testing)
            for hunk in file:
                lines = list(hunk.target_lines())
                for i, line in enumerate(lines):
                    if todo := is_todo_line(line, file_todos, self.testing):
                        print(todo)

    def _extract_issue_from_inline_todo(self, line, i, lines, hunk, file):
        """Checks whether the inline todo is single-line or multi-line."""
        if lines := is_multiline_todo(line, i, lines):
            return self._extract_issue_from_multi_line_todo(line, lines, hunk, file)
        return self._extract_issue_from_single_line_todo(line, hunk, file)

    def _extract_issue_from_docstring_todo(self, line, i, lines, hunk, file):
        """Uses napoleon to get todo sections of docstrings of changed files"""
        raise NotImplementedError()

    def _extract_issue_from_single_line_todo(self, line, hunk, file):
        clean_line = strip_line(line)
        if clean_line.startswith('('):
            assignees = [elem.strip() for elem in clean_line[clean_line.index("(") + 1:clean_line.rindex(")")].split(',')]
            clean_line = clean_line.split(')')[-1]
        else:
            assignees = []
        if line.line_type == '+':
            status = LineStatus.ADDED
        else:
            status = LineStatus.DELETED
        issue = Issue(
            title=clean_line,
            labels=['todo'],
            assignees=assignees,
            milestone=None,
            body="",
            hunk=hunk.target,
            file_name=file.target_file,
            start_line=line.target_line_no,
            markdown_language='python',
            status=status
        )
        self.issues.append(issue)

    def _extract_issue_from_multi_line_todo(self, line, lines, hunk, file):
        """Creates issue with info from multi-line todo"""
        lines, assignees = _get_assignees(lines)
        lines, labels = _get_labels(lines)
        lines, milestone = _get_milestone(lines)
        if line.line_type == '+':
            status = LineStatus.ADDED
        else:
            status = LineStatus.DELETED
        try:
            title, body = lines[0], lines[1:]
        except IndexError:
            title = lines[0]
            body = ""
        issue = Issue(
            title=title,
            labels=['todo'] + labels,
            assignees=assignees,
            milestone=milestone,
            body=body,
            hunk=hunk.target,
            file_name=file.target_file,
            start_line=line.target_line_no,
            markdown_language='python',
            status=status
        )
        self.issues.append(issue)

    def build_issue_from_files(self):
        pass


def is_todo_line(line, todos, testing=False):
    """Two cases: Line starts with any combination of # Todo, or line starts with
    asterisk and is inside a napoleon docstring todo header.

    Also filter out # todo: +SKIP.

    Args:
        line (Unidiff.Line): A line instance.
        todos (list[str]): Todos from the file.

    Keyword Args:
        testing (bool, optional): Set True for Testing. Defaults to False.

    """
    if re.match(INLINE_TODO_PATTERN, line.value, re.MULTILINE) and not TODO_SKIP_SUBSTRING in line.value:
        line = line.value.replace('#', '')
    elif re.match(DOCSTRING_TODO_PATTERN, line.value, re.MULTILINE) and not TODO_SKIP_SUBSTRING in line.value:
        line = line.value.replace('*', '').strip()
        check = [line in t for t in todos]
        if any(check):
            index = check.index(True)
            block = todos[index]
            return block
    else:
        return False
    return line.strip()


def extract_todos_from_file(file, testing=False):
    """Parses a file and extracts todos in google-style formatted docstrings.

    Args:
        file (str): Path to a file.

    Keyword Args:
        testing (bool, optional): If set to True todos containing `# todo: +SKIP`
            will be disregarded. Defaults to False.

    Returns:
        list[str]: A list containing the todos from this file.

    """
    if testing:
        file = 'tests/examples_base.py'
    file = file.replace('b/', '')

    # use ast to parse
    docs = []
    with open(file, 'r') as f:
        parsed_file = ast.parse(f.read())
    try:
        docs.append(ast.get_docstring(parsed_file))
    except Exception as e:
        raise Exception("Exclude this specific exception") from e
    for node in parsed_file.body:
        try:
            docs.append(ast.get_docstring(node))
        except TypeError:
            pass

    # append todos in list:
    todos = []
    for doc in docs:
        if doc is None:
            continue
        blocks = doc.split('\n\n')
        for block in blocks:
            if 'Todo:' in block:
                block = '\n'.join(block.splitlines()[1:])
                block = block.split('* ')[1:]
                block = [re.sub(' +', ' ', s) for s in block]
                if not testing:
                    block = list(filter(lambda x: False if TODO_SKIP_SUBSTRING in x else True, block))
                todos.extend(block)
    return todos


def is_multiline_todo(line, i, lines):
    if 'todo' in line.value.lower():
        out = [strip_line(line, with_todo=True)]
    else:
        out = [strip_line(line)]
    for trailing_line in lines[i + 1:]:
        if len(strip_line(trailing_line, with_whitespace=False)) - len(strip_line(trailing_line, with_whitespace=False).lstrip()) == 2:
            out.append(strip_line(trailing_line, with_whitespace=True))
    if len(out) > 1:
        return out
    return False


def strip_line(line, with_whitespace=True, with_todo=True):
    if with_whitespace:
        line = line.value.strip().lstrip('#').lstrip()
    else:
        line = line.value.strip().lstrip('#')
    if with_todo:
        return re.sub(r'(?i)todo\s', '', line)
    else:
        return line


def parse_todo(lines):
    pass


################################################################################
# Main
################################################################################

def main(testing):
    if testing:
        print("Running in Test Mode")
    print("Running Main")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Python code Todos to github issues.")
    parser.add_argument('--testing', dest='testing', action='store_true', help="Whether a testing run is executed and tests will be conducted.")
    parser.set_defaults(testing=False)
    args = parser.parse_args()
    main(testing=args.testing)
