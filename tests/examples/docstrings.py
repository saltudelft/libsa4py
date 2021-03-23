def basic_docstring():
    """This is a basic docstring"""
    pass


# A function with Google-style docstring
def google_docstring(param1, param2):
    """Summary line.

    Extended description of function.

    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter.

    Returns:
        bool: Description of return value
    """
    if len(param2) == param1:
        return True
    else:
        return False


# A function with a reST docstring
def rest_docstring(param1, param2):
    """
    Summary line.

    Description of function.

    :param int param1: The first parameter.
    :param str param2: The second parameter.
    :type param1: int
    :return: Description of return value
    :rtype: bool
    """
    if len(param2) == param1:
        return True
    else:
        return False


# A function with a NumPy-style docstring
def numpy_docstring(param1 , param2):
    """
    Summary line.

    Extended description of function.

    Parameters
    ----------
    param1 : int
        The first parameter.
    param2 : str
        The second parameter.

    Returns
    -------
    bool
        Description of return value

    See Also
    --------
    google_docstring : Same function but other docstring.

    Examples
    --------
    numpy_docstring(5, "hello")
        this will return true
    """
    if len(param2) == param1:
        return True
    else:
        return False


# A function with no docstring
def no_docstring():
    return None
