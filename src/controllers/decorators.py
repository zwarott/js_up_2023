import functools
from time import time


def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time()
        result = func(*args, **kwargs)
        duration = time() - start_time
        separator = "-" * 150
        print(separator, f"Checking time: {duration:.4f} s.", separator, sep="\n")
        return result

    return wrapper
