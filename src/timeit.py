#!/usr/bin/env python3

from time import time
from functools import wraps
from typing import Any
from collections.abc import Callable


def time_it(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args: int, **kwargs: int) -> Any:
        start = time()
        result = func(*args, **kwargs)
        end = time()
        run_time: float = round(end - start, 3)
        return result, run_time

    return wrapper
