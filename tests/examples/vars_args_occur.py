"""
This file contains various forms of variable and arguments usage for testing (i.e. contextual usage)
"""

from .different_fns import add


PI = 3.14
MOD_CONSTANT: int = 404


class TestVarArgOccur:

    greeting: str = 'Hello'
    num = 128
    cls_constant = MOD_CONSTANT + 200

    def __init__(self, x: int, y):
        self.x = x
        self.y = y

    def fn_params_occur(self, param1: int, param2: int):
        z = param1 + param2

        add_x_y = add(param1, param2)

        list_comp = [i for i in range(param1 ** param2 * z)]

        if param1 * add_x_y == 2:
            pass
        elif param1 % param2 < 5:
            pass

        while param2 * param1 * z // 2:
            pass

        for i in range(param1 + z * 2):
            pass

        with z * param2 as f:
            print(z ** param2 / f)

        assert param1 == add_x_y * z
        yield z + param2
        return param1 + 2 + param2 / 5

    def local_vars_usage(self, p):
        v: int = sum([1, 2, 3, 4])
        v_1 = v + p + 10

        for i in range(0, v + v_1):
            i += v + 2
            yield i + v_1

        if v < 20 and v_1 + v > 50:
            print(v)

        elif v * v_1 != 50:
            print(v * v_1)
        else:
            print(v_1)

        while v + v_1 < p:
            v *= 5 + v_1

        with (v_1 + p // 2) as n:
            assert v != n

        return v + p + p + 20

    # Class variable usage in various context
    def class_vars_usage(self):
        c = self.x + TestVarArgOccur.num

        if TestVarArgOccur.num + c < 3.0:
            pass

        for i in range(0, TestVarArgOccur.num):
            yield TestVarArgOccur.num + i

        while TestVarArgOccur.num < 4:
            TestVarArgOccur.num -= 8

        with (TestVarArgOccur.greeting + "World!") as f:
            pass

        assert c != TestVarArgOccur.cls_constant

        return TestVarArgOccur.cls_constant + c

    # Module-level variable usage in various context
    def module_vars_usage(self, add_something):
        if PI + add_something > 3.0:
            pass

        for i in range(0, int(PI)):
            pass

        while PI + MOD_CONSTANT > 1.0:
            PI =- 1 + add_something

        with (MOD_CONSTANT + PI + add_something) as n:
            print(n)

    def formatted_str(self, p):
        x = 12
        y = 3.2
        print(f"The calculated number is {x * y // p} and ...")
