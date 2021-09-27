# Change Log for kevinsawade/python-todo-to-issue

Dateformat: yyyy-mm-dd

[1.0.4] - 2021-09-27

# Todos after code-lines working.

## Changed

The arg can be set in the yaml as `${{ true }}`, `true` or `True` and the `GitHubClient` class checks accordingly.
Fixed a mistake in `action.yaml`

## Added

Workflow now prints, whether it runs in after-code-todo mode or not.

[1.0.3] - 2021-09-22

# Fixed skipping of todos

## Changed

Todos previously could be skipped with `# todo: +SKIP`, but from now on, this will be done by `todo: +SKIP`. This was done because all todos are comments anyways.

## Added

Added info about the skipping and todo_after_code feature to README.md

[1.0.2] - 2021-09-22

# Todos from anywhere in lines

## Added

Can now read todos from anywhere in code lines. Per default this option is set to true.
This option can be activated by setting the variable `INCLUDE_TODO_AFTER_CODE_LINE` in the workflow.yaml file to true:

```yaml
steps:
      - name: Checkout 🛎️
        uses: actions/checkout@v2

      - name: Create Issues ✔️
        uses: kevinsawade/python-todo-to-issue@latest
        with:
          TOKEN: ${{ secrets.GITHUB_TOKEN }}
          INCLUDE_TODO_AFTER_CODE_LINE: ${{ true }}
```

[1.0.0] - 2021-07-13

# Initial Release

## Added
Parses diffs, and gets files at defined commits via api.github.com.
Recognizes in-line todos and google-docstring style todos.
Opens and closes issues.
Tags working.
Assignees working.

## Needs fixing
Milestones not working.
