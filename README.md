![Unittests](https://github.com/kevinsawade/python-todo-to-issue/actions/workflows/unittests.yml/badge.svg)
[![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/kevinsawade/5989424e030f59c478f353d5b9da91c2/raw/test.json)](https://kevinsawade.github.io/python-todo-to-issue/htmlcov/index.html)

# python-todo-to-issue

A repository containing a github action that scans diffs for todos and creates issues from them. This action only works for python files. I took inspiration from Alastair Mooney's todo to issue action (https://github.com/alstr/todo-to-issue-action) and added capabilities for checking google-style docstrings for todos. Please also check out his repository if you want to use this feature for other languages than python.

# Quickstart

- Create a file at `.github/workflows/todo-to-issue.yml` with this content:

```yaml
name: Todo-to-Issue

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  todo-to-issue:
    # The type of runner that the job will run on
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9]

    steps:
      - name: Checkout 🛎️
        uses: actions/checkout@v2

      - name: Create Issues ✔️
        uses: kevinsawade/python-todo-to-issue@latest
        with:
          TOKEN: ${{ secrets.GITHUB_TOKEN }}
          # you can let your own bot create issues by supplying:
          # TOKEN: ${{ secrets.CUSTOM_ISSUE_TOKEN }}
```

## Write Todos

Now you can start writing todos and they will be raised as issues, when you push to github:

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

Besides these in-line todos, google-style docstring todos will also be picked up.

```python
def myfunc(arg1):
    """This is the overview docstring.
    
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
    """
    return 'Hello' + arg1
```

## Let your own bot create the issues.

Please refer to the documentation on https://kevinsawade.github.io/python-todo-to-issue/index.html for this use case.

## Todos after code

If you write your todos after code lines like so:

```python

a = str(1) # todo: This line is bad code
b = '2' # todo (kevinsawade): This line is better.
```

You can add these after-code-todos with an additional option to the yaml file:

```yaml
- name: Create Issues ✔️
        uses: kevinsawade/python-todo-to-issue@latest
        with:
          TOKEN: ${{ secrets.GITHUB_TOKEN }}
          INCLUDE_TODO_AFTER_CODE_LINE: ${{ true }}
```

## Skipping todos

If you want todos to not be raised as issues: Add `todo: +SKIP` somewhere in the line.

```python
print(a)
# todo: Print more info todo: +SKIP
```

# Documentation

Visit the documentation under https://kevinsawade.github.io/python-todo-to-issue/index.html
