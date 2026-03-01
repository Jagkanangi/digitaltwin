import logging
from functools import wraps
from pydantic import BaseModel
import inspect

def _format_arg(arg):
    if isinstance(arg, BaseModel):
        try:
            return arg.model_dump()
        except Exception as e:
            return f"Pydantic model of type {type(arg).__name__} could not be serialized: {e}"
    return repr(arg)

def log(func):
    """
    A decorator that logs the parameters and return value of a function.
    If an argument is a Pydantic model, it will be dumped to a dict for logging.
    'self' arguments are ignored.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        bound_args = inspect.signature(func).bind(*args, **kwargs)
        bound_args.apply_defaults()

        args_to_log = []
        for name, value in bound_args.arguments.items():
            if name == 'self':
                continue
            args_to_log.append(f"{name}={_format_arg(value)}")

        signature = ", ".join(args_to_log)
        logger.info(f"Calling {func.__name__}({signature})")
        
        # Call the actual function
        try:
            result = func(*args, **kwargs)
            # Log the return value
            logger.info(f"{func.__name__} returned {_format_arg(result)}")
            return result
        except Exception as e:
            logger.exception(f"Exception raised in {func.__name__}. exception: {str(e)}")
            raise e
    return wrapper

def log_vo(func):
    """
    A decorator that logs only Pydantic model arguments from the 'vo' package.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        bound_args = inspect.signature(func).bind(*args, **kwargs)
        bound_args.apply_defaults()

        args_to_log = []
        for name, value in bound_args.arguments.items():
            if name == 'self':
                continue
            if isinstance(value, BaseModel) and value.__class__.__module__.startswith('vo'):
                args_to_log.append(f"{name}={_format_arg(value)}")
        
        if args_to_log:
            signature = ", ".join(args_to_log)
            logger.info(f"Calling {func.__name__} with vo models: ({signature})")

        # Call the actual function
        try:
            result = func(*args, **kwargs)
            # Log the return value if it's a vo model
            if isinstance(result, BaseModel) and result.__class__.__module__.startswith('vo'):
                logger.info(f"{func.__name__} returned vo model: {_format_arg(result)}")
            return result
        except Exception as e:
            logger.exception(f"Exception raised in {func.__name__}. exception: {str(e)}")
            raise e
    return wrapper
