import functools
from time import time
from types import FunctionType


def timer(func: FunctionType):
    """
    Timer decorator for capturing process time.

    Parameters
    ----------
    func : FunctionType
        A function on which will be this decorator
        applied.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time()
        result = func(*args, **kwargs)
        duration = time() - start_time
        separator = "-" * 150
        print(separator, f"Checking time: {duration:.4f} s.", separator, sep="\n")
        return result

    return wrapper
