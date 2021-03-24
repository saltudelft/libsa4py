"""
An example for testing the removal of comments and docstrings from the file
"""

# A comment
x = 12  # Variable

# A multi line comment
# A multi line comment
# A multi line comment

def delta():
    """
    Docstring for a function
    """
    pass


class Foo:
    """
    Docstring for a class
    """

    def bar(self):
        """
        Docstring for class method
        """
        # Let's pass!
        pass
