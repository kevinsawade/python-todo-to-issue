import unittest
import os

class TestTodoToIssue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if 'INPUT_TOKEN' in os.environ:
            print("Environment token was already in env.")
        else:
            print("Setting environment token.")
            try:
                with open('act.vault', 'r') as f:
                    gh_token = f.readline().rstrip('\n').split('=')[1]
            except FileNotFoundError as e:
                s = ("Could not retrieve github token. There are two ways of fixing this.",
                     "Both of these possibilities include creating a file named `act.vault`",
                     "At repo root. This unittest class tries to read this file., so make",
                     "sure that it contains this line: `GITHUB_TOKEN=ghp_******`. If you run:",
                     "This action within nektos/act, please provide the `act.vault` file with",
                     "The `--secret-file` option to nektos/act.")
                new_exc = Exception(s)
                raise new_exc from e
            os.environ['INPUT_TOKEN'] = gh_token
            print("Environment token set up.")

        os.environ['INPUT_REPO'] = 'kevinsawade/python-todo-to-issue'
        os.environ['INPUT_BEFORE'] = '11858e41'
        os.environ['INPUT_SHA'] = '036ef2ca'

        # print some info
        print("I will attempt to print it. But based on where you run this line from, it will not print")
        print(f"Here it is ---> {os.environ['INPUT_TOKEN']} <---")

    @classmethod
    def tearDownClass(cls):
        del os.environ['INPUT_TOKEN']
        if 'INPUT_REPO' in os.environ:
            del os.environ['INPUT_REPO']
            del os.environ['INPUT_BEFORE']
            del os.environ['INPUT_SHA']
        print("\nDeleting environment token.")

    def test_read_issues(self):
        from main import GitHubClient
        client = GitHubClient(testing=1)
        print(client.issues_url)
        self.assertTrue(any([issue['title'] == 'TESTING ISSUES' for issue in client.existing_issues]))
        self.assertTrue(any([issue['assignee']['login'] == 'kevinsawade' for issue in client.existing_issues if  issue['assignee'] is not None]))

    def test_issue_missing_arguments(self):
        from main import Issue
        with self.assertRaises(TypeError):
            issue = Issue(title='THIS IS A TESTING TITLE')

    def test_create_and_close_issue(self):
        from main import GitHubClient, Issue
        client = GitHubClient(testing=1)
        issue = Issue(testing=1)
        client.create_issue(issue)
        client = GitHubClient(testing=1)
        self.assertTrue(any([issue['title'] == 'TEST AUTO ISSUE' for issue in client.existing_issues]))
        client.close_issue(issue)
        client = GitHubClient(testing=1)
        self.assertTrue(all([issue['title'] != 'TEST AUTO ISSUE' for issue in client.existing_issues]))

    def test_find_todos(self):
        from main import TodoParser, LineStatus
        parser = TodoParser(testing=1)
        issues = parser.issues
        self.assertEqual(issues[0].title, 'Single-line Todo. Add more documentation.')
        self.assertEqual(issues[1].title, 'We should also add some actual code.')
        self.assertEqual(issues[3].title, 'I will add many.')
        self.assertEqual(issues[1].assignees, ['kevinsawade'])
        self.assertEqual(issues[13].title, 'Multi-line todos should follow google-styleguide like this one.')
        self.assertEqual(issues[13].assignees, ['github_user2', 'user3'])
        self.assertEqual(issues[13].labels, ['todo', 'wontfix', 'devel'])

        parser = TodoParser(testing=2)
        issues = parser.issues
        deleted = LineStatus.DELETED
        self.assertEqual(issues[0].title, 'I will add many.')
        self.assertTrue(issues[0].status is deleted)

    def test_unmatched_docstring_quotes(self):
        from main import TodoParser, get_body
        parser = TodoParser(testing=1)
        issues = parser.issues
        body = get_body(issues[1], 'url', line_break='\n')
        self.assertEqual(body.count('"""'), 2)

    def test_open_and_close_complex_issue_one(self):
        from main import GitHubClient, TodoParser
        parser = TodoParser(testing=1)
        issue = parser.issues[-3]
        client = GitHubClient(testing=1)
        client.create_issue(issue)
        parser = TodoParser(testing=2)
        issue = parser.issues[-2]
        client = GitHubClient(testing=2)
        self.assertTrue(any([issue['title'] == 'Write some more methods.' for issue in client.existing_issues]), msg=client.existing_issues)
        status_codes = client.close_issue(issue)
        client = GitHubClient(testing=1)
        self.assertTrue(all([issue['title'] != 'Write some more methods.' for issue in client.existing_issues]), msg=status_codes)

    def test_open_and_close_complex_issue_two(self):
        from main import GitHubClient, TodoParser
        parser = TodoParser(testing=1)
        issue = parser.issues[-5]
        client = GitHubClient(testing=1)
        client.create_issue(issue)
        parser = TodoParser(testing=2)
        issue = parser.issues[-3]
        client = GitHubClient(testing=2)
        self.assertTrue(any([issue['title'] == 'Multi-line todos should follow google-styleguide like this one.' for issue in client.existing_issues]), msg=client.existing_issues)
        status_codes = client.close_issue(issue)
        client = GitHubClient(testing=2)
        self.assertTrue(all([issue['title'] != 'Multi-line todos should follow google-styleguide like this one.' for issue in client.existing_issues]), msg=status_codes)

    def test_duplicate_issue_raise(self):
        from main import GitHubClient, Issue
        issue = Issue(testing=1)
        issue.title = 'TESTING ISSUES'
        issue.body = ['This is an issue that will be checked when the app runs in testing mode.']
        client = GitHubClient(testing=1)
        client.create_issue(issue)
        client = GitHubClient(testing=1)
        title = 'TESTING ISSUES'
        titles = [issue['title'] for issue in client.existing_issues]
        self.assertEqual(titles.count(title), 1)

    def test_skip_todo(self):
        from main import extract_todos_from_file
        with open('main.py', 'r') as f:
            todos = extract_todos_from_file(f.read().split('# Globals\n')[1])
        self.assertEqual(todos, [])

