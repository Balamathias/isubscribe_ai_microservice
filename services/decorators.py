from functools import wraps

def requires_user(fn):
    """
    Decorator to mark a tool-function as needing `user` injected
    as its first argument.
    """
    fn._requires_user = True
    return fn
