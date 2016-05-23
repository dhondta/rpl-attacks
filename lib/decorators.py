# -*- coding: utf8 -*-
from functools import wraps
from inspect import getargspec, signature
from os.path import dirname, join

from .logconfig import logging


# **************************************** PATH-RELATED DECORATORS ****************************************
def expand_file(inside=None, ensure_ext=None):
    """
    This decorator expands the path to the specified filename. If this filename is not already a path,
     expand it to specified folder 'inside'. If an extension is to be ensured, check and add it if relevant.

    :param fn: input filename
    :param inside: folder to expand in order to build filename's path (if not already specified in filename)
    :param ensure_ext: extension to be ensured for the file
    :return: the decorator with the first argument replaced with its expanded path
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            fn = args[0]
            if dirname(fn) == '':
                fn = join(inside, fn)
            if ensure_ext and not fn.endswith("." + ensure_ext):
                fn += "." + ensure_ext
            args = (fn,) + args[1:]
            return f(*args, **kwargs)
        return wrapper
    return decorator


def expand_folder(nargs):
    """
    This decorator expands folder paths (up to the nth arguments) if these are in the form
     of a tuple.

    :param nargs: number of heading arguments on which the wrapper is to be applied
    :return: the decorator with the nargs first arguments replaced with their expanded paths
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            margs = []
            for i in range(nargs):
                if isinstance(args[i], (tuple, list)):
                    margs.append(join(*args[i]))
                else:
                    margs.append(args[i])
            args = tuple(margs) + args[nargs:]
            return f(*args, **kwargs)
        return wrapper
    return decorator


# ******************************************** TASK DECORATORS ********************************************
def report_bad_input(f):
    """
    This decorator catchs f's signature and checks for bad input arguments in order to pretty report
     them in a customized way.

    :param f: the decorated function
    :return: the wrapper with its original arguments or exit with return code 2 if bad arguments
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        sig = getargspec(f)
        n = len(sig.args[:-len(sig.defaults)]) if sig.defaults else len(sig.args)
        if len(args) < n:
            logging.critical("Bad input arguments !")
            logging.info("This command has the following signature: {}{}".format(f.__name__, str(signature(f))))
            logging.info("Please check the documentation for more information.")
            exit(2)
        else:
            return f(*args, **kwargs)
    return wrapper


# *************************************** COMMAND LOGGING DECORATORS ***************************************
def stderr(f):
    """
    This simple decorator appends bash command tail for catching stderr, executes the input function, then
     checks for the return_code from the executed command's output and logs (filtered) stderr before
     exiting if relevant.

    :param f: the decorated function
    :return: the wrapper
    """
    @wraps(f)
    def wrapper(cmd, *args, **kwargs):
        out = f(cmd + ' 2>&1 /dev/null', *args, **kwargs)
        if out.return_code != 0:
            filtered = []
            for line in out.split('\n'):
                if any([line.startswith(s) for s in ['cp ', 'mkdir ', '  CC', '  AR']]) or 'warning' in line:
                    continue
                filtered.append(line)
            logging.critical("Command '{}' failed with the following error:\n".format(cmd) + '\n'.join(filtered))
            exit(1)
    return wrapper
