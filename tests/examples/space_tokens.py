"""
This module's purpose is to test SpaceAdder, which helps tokenization of source code
"""
from typing import List
import math as m

CONSTANT:int=10
STRING="Hello, World!"

"Hello, ""World"==STRING

d={k:v for k,v in [(1,2),(2,3)]}
d_e={**d,**d}

f_str=f"Blah blah{STRING+STRING}"

l:List[ int ]=[1,2,3,4]

print(l[1])

class Delta:
    def __init__(self):
        self.x='nothing'

def foo(x,y,*s):
    global CONSTANT
    n=10
    n//=n%x
    y%=x;x**=n
    if x|x&y|~y|x^y:
        x<<y
        y>>x
        s<<=x
        x>>=y
        y&=x
        x|=y
        x^=y
    if x<=y or y>=x and~x:
        pass

    assert x!=y

    return n+x//y

@set
def bar(x:int)->int:
    v=foo(x,12)
    try:
        v/=x
    except ZeroDivisionError:
        raise RuntimeError
    finally:
        pass
    if x<v and v>x:
        x*=x
    else:
        pass
    del x
    return v

for i in range(CONSTANT+10+bar(10)):
    if i+foo(i,10)+2:
        print(i/i)
        i+=2-3**12
        i-=4
    while i<100:
        i=i+1

    with (i+3) as w:
        pass

foo(1,2,*l)