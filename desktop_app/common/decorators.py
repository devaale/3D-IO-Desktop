from timeit import default_timer as timer
from .logger import logger
import threading
import functools


def timing(f):
    @functools.wraps(f)
    def wrap(*args, **kw):
        ts = timer()
        result = f(*args, **kw)
        te = timer()
        # print("Function: " + str(f.__name__) + ", Total time : %.1f ms" % (1000 * (te - ts)))
        logger.info("Function: " + str(f.__name__) + ", Total time : " + str((1000 * (te - ts))) + " ms")
        return result
    return wrap

def synchronized(wrapped):
    lock = threading.Lock()
    @functools.wraps(wrapped)
    def _wrap(*args, **kwargs):
        with lock:
            return wrapped(*args, **kwargs)
    return _wrap
