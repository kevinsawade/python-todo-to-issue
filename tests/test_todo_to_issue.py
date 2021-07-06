import unittest
import os

class TestTodoToIssue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.putenv('INPUT_REPO', 'kevinsawade/python-todo-to-issue')
        os.putenv('INPUT_BEFORE', 'auto')
        os.putenv('INPUT_SHA', 'auto')
        try:
            exec('gh_token = "' + open('secrets', 'r').read().splitlines()[0] + '"', globals(), globals())
        except FileNotFoundError as e:
            new_exc = Exception("Put a file named `secrets` at repo root and put your github secret with repo access rights into there.")
            raise new_exc from e
        print(gh_token)
        os.putenv('INPUT_SECRET', gh_token)

    @classmethod
    def tearDownClass(cls):
        print("Deleting environment variables")

    def test_read_issues(self):
        print("Reading issues")

