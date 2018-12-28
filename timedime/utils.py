"""
Generic utilities file.
"""

from functools import reduce

# https://stackoverflow.com/questions/16739290

def splat(f):
    """pre-splat an argument into a function and return the new lambda"""
    return lambda x: f(*x)

def compose2(f, g):
    return lambda *a, **kw: f(g(*a, **kw))

def compose(*fs):
    return reduce(compose2, fs)
