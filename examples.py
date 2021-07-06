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
    * If we want to have multi-line Todos, we have
        to indent with 4 spaces. And assignees are added
        like so:.
        assignees: kevin
        labels: devel
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


"""

def unfinished_func():
    """Function-level docstring.

    More info about the function in an explanatory text.

    Todo:
        * (kevin) This function is empty. Put something here.

    """
    # This is a simple in-line comment
    # Function will be passed, but I will also add todos:
    pass

class useless_class:
    """
    Todo:
        * Write some more methods.

    """
    def __init__(self):
        pass

    @property
    def random(self):
        # TODO (kevin): This property is not random
        return 2
