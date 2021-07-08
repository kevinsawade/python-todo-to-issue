import unittest
import os

class TestTodoToIssue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            with open('secrets', 'r') as f:
                gh_token = f.readline()
        except FileNotFoundError as e:
            new_exc = Exception("Put a file named `secrets` at repo root and put your github secret (no quotation marks, just plain text) with repo access rights into there. Usually they start with gh_")
            raise new_exc from e
        os.environ['INPUT_TOKEN'] = gh_token

    @classmethod
    def tearDownClass(cls):
        del os.environ['INPUT_TOKEN']

    @unittest.skip("Avoid too many closed issues during development")
    def test_read_issues(self):
        from main import GitHubClient
        client = GitHubClient(testing=True)
        self.assertTrue(any([issue['title'] == 'TESTING ISSUES' for issue in client.existing_issues]))
        self.assertTrue(any([issue['assignee']['login'] == 'kevinsawade' for issue in client.existing_issues if  issue['assignee'] is not None]))

    @unittest.skip("Avoid too many closed issues during development")
    def test_issue_missing_arguments(self):
        from main import Issue
        with self.assertRaises(TypeError):
            issue = Issue(title='THIS IS A TESTING TITLE')

    @unittest.skip("Avoid too many closed issues during development")
    def test_create_and_close_issue(self):
        from main import GitHubClient, Issue
        client = GitHubClient(testing=True)
        issue = Issue(testing=True)
        client.create_issue(issue)
        client = GitHubClient(testing=True)
        self.assertTrue(any([issue['title'] == 'TEST AUTO ISSUE' for issue in client.existing_issues]))
        client.close_issue(issue)
        client = GitHubClient(testing=True)
        self.assertTrue(all([issue['title'] != 'TEST AUTO ISSUE' for issue in client.existing_issues]))

    def test_find_todos(self):
        from main import TodoParser
        parser = TodoParser(testing=True)
        print(parser.issues)
        self.assertTrue(False)

