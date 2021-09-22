# Change Log for kevinsawade/python-todo-to-issue

Dateformat: yyyy-mm-dd

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
