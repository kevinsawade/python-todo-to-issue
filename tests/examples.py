############
# DISCLAIMER
# AND
# LICENSING
# INFO
###########
"""Module level Docstring.

Examples:
    This is just a text. The example happens here::

        >>> import main as main
        >>> # This is a comment
        >>> # TODO This is a todo.
        >>> #  assignees: kevin
        >>> #  labels: devel


Todo:
    * Single-line Todo. Add more documentation.
    * (kevinsawade) We should also add some actual code.
    * Multi-line todos should follow google-styleguide.
        This means a tab should be used indentation inside
        the docstrings. This will form the body of the issue.
        Assignees and labels can be added the same way:
        assignees: github_user2, user3
        labels: wontfix, devel
        milestones: alpha
    * I will add many.
    * New lines, so that
    * (kevin) has to use astparse
    * To check whether added  bullrt
    * points will move
    * out of the todo block.
    * Which would require to check all
    * lines starting with the asterisk
    * I think I will stop now
    * I will also delete some todos from down there.
    * Multi-line todos should follow google-styleguide like this one.
        This means a tab should be used indentation inside
        the docstrings. This will form the body of the issue. Change!.
        Assignees and labels can be added the same way:
        assignees: github_user2, user3
        labels: wontfix, devel
        milestones: alpha


"""


def unfinished_func():
    """Function-level docstring.

    More info about the function in an explanatory text.

    Todo:
        * (kevinsawade) This function is empty. Put something here.
        * Multi-line todos should follow google-styleguide like this one.
            This means a tab should be used indentation inside
            the docstrings. This will form the body of the issue. Change!.
            Assignees and labels can be added the same way:
            assignees: github_user2, user3
            labels: wontfix, devel
            milestones: alpha

    """
    # This is a simple in-line comment
    # Function will be passed, but I will also add todos:
    # Todo (kevinsawade): Fill this function.
    pass


class useless_class:
    """
    Todo:
        * (kevinsawade) Write some more methods.

    """

    def __init__(self):
        # TODO: This property is not random.
        #  Change it around and make it random.
        #  assignees: kevinsawade
        #  labels: wontfix
        pass

    @property
    def random(self):
        # TODO: This property is not random.
        #  Change it around and make it random.
        #  assignees: kevinsawade
        #  labels: wontfix
        return 2
