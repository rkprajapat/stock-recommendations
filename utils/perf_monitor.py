# # Copyright (C) KonaAI - All Rights Reserved

"""Provides performance monitoring decorator
"""

import sys
import time
from functools import wraps

from utils.custom_logger import perLogger

# This is a decorator that monitors total time and memory taken by a function


def monitor_performance(func):
    """Performance monitoring function

    Args:
        func (object): function being monitored
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        star_memory = sys.getsizeof(func)
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        end_memory = sys.getsizeof(func)

        total_time = round(end_time - start_time, 4)
        total_memory = end_memory - star_memory

        perLogger.perflog(total_time, total_memory, func.__qualname__)

        return result

    return wrapper
