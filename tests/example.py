"""
This is an example script for testing LibCST extractor
"""

from typing import Optional, List

PI = 3.14
TEST_CONSTANT: int = 404

LONG_STRING = """Vestibulum dignissim nisi in ex vehicula viverra at et augue. Phasellus volutpat euismod gravida.
 Proin condimentum mattis consequat. Integer lobortis orci et risus iaculis mattis. Fusce at urna semper, lobortis
  massa in, fringilla ante. Morbi sed tortor bibendum, venenatis diam in, interdum odio. Lorem ipsum dolor sit amet,
   consectetur adipiscing elit. Quisque volutpat sapien sed odio eleifend elementum."""


def add_special(self, name): ...

class Test:

    # A comment
    out_x = 12
    out_u, out_f = 14, 'tests'
    out_y: str = 'Hello'
    scientific_num = 1.3e+4

    def __init__(self, x: int) -> None:
        self.x: int = x
        self.u = "Test"
        self.j = 12.3
        y: float = 3.14
        w: List[str] = ['hi', 'world']
        z = 3
        foo: str
        self.b, self.c = 45, 'blah'
        self.error: List

    def add(self, y: int) -> int:
        """This function adds some number to y"""
        return y + self.x

    def return_optional(self, y: List[List[(int, int)]]) -> Optional[int]:
        if y[0][0] == 5:
            return None
        return y

    async def add_async(self, y: int) -> int:
        """This is an async function"""
        return await y + self.x

    def noargs() -> int:
        """This function has no input arguments"""
        return 5

    def noreturn(x: int):
        """This function has no typed return"""
        print(x)

    def return_none(x: int) -> None:
        """This function returns None"""
        print(x)

    def untyped_args(x: int, y) -> int:
        """This function has an untyped input argument"""
        return x + y

    def type_in_comments(x, y):
        # type: (int, int) -> int
        return x + y

    def with_inner(self) -> int:
        """This function has an inner function"""
        def inner() -> int:
            """This is the inner function"""
            return 12
        return inner()

    def varargs(self, msg: str, *xs: int) -> int:
        """This function has args as well as varargs"""
        sum: int = 0
        for x in xs:
            sum += x
        print(msg)
        return sum + self.x

    def untyped_varargs(self, msg: str, *xs) -> int:
        """This function has untype varargs"""
        sum: int = 0
        for x in xs:
            sum += x
        print(msg)
        return sum + self.x

    def google_docstring(self, param1: int, param2: str) -> bool:
        """Summary line.

        Extended description of function.

        Args:
            param1 (int): The first parameter.
            param2 (str): The second parameter.

        Returns:
            bool: Description of return value"""
        if len(param2) == param1:
            return True
        else:
            return False

    def rest_docstring(self, param1: int, param2: str) -> bool:
        """
        Summary line.

        Description of function.

        :param int param1:  The first parameter.
        :param str param2: The second parameter.
        :type param1: int
        :return: Description of return value
        :rtype: bool
        """
        if len(param2) == param1:
            return True
        else:
            return False

    # def walrus_op(self):
    #
    #     while (n := 4):
    #         print(n)

    def numpy_docstring(self, param1: int, param2: str) -> bool:
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

    def nested_parameterized(list_param: List[List[List[List[int]]]]) -> Optional[Optional[Optional[int]]]:
        return None
    
    def no_docstring(param1: int) -> int:
        try:
            return 5
        except:
            return 4

    def formatted_str(self):
        x = 12
        y = 3.2
        print(f"The calculated number is {x * y} and ...")

    def ext_names_tuple(self):
        t_1, (t_2, t_3) = 1, (2, 3)

    def test_pyre_types(self):
        l = [1, 2, 3]

        return ['test']

    def tuple_assigns(self):
        x, y, z = 12, 0.5, 34
        a, (b, c) = 1, (2, 3)
        d, ((e, f), (g, h)) = 4, ((5, 6), (6, 7))

    def class_var_usage(self, y):

        if Test.scientific_num + y < 3.0:
            pass

        for i in range(0, Test.out_x):
            pass

    def module_var_usage(self, add_something):
        if PI + add_something > 3.0:
            pass

        for i in range(0, int(PI)):
            pass

        while PI + TEST_CONSTANT > 1.0:
            PI =- 1 + add_something


class Test2:
    f_odd = 5
    y: float = 3.14

    def no_params():
        return 0

    def no_return(x: int):
        pass

    def docstring_only():
        """"""

    def basic_string_docstring():
        "string"

    def single_expression(self):
        5 + 7

    def single_literal(self):
        6

    def kwarg_method(a: int, *b: int, **c: float):
        return c

    def args_occur(self, x: int, y: int):
        z = x + y

        add_x_y = add_numbers(x, y)

        list_comp = [i for i in range(x ** y * z)]

        if Test2.x * TEST_CONSTANT == 2:
            pass
        elif Test2.y % TEST_CONSTANT < 5:
            pass

        while y * x * z * TEST_CONSTANT // 2:
            pass

        for i in range(x + z * 2):
            pass

        with z * y as f:
            pass

        assert x == add_x_y * z
        yield z + y
        return x + 2 + y / 5


def add_numbers(x: int, y: int) -> int:
    """This function has an untyped input argument"""
    z: int = x + y
    return x + y
