# -*- coding: utf8 -*-
from cmd import Cmd
from funcsigs import signature
from functools import wraps
from os.path import dirname, join
from sys import exit

from .behaviors import DefaultCommand
from .logconfig import logging


# ************************************* GENERIC COMMAND DECORATORS **************************************
def command(**kwargs):
    """
    This decorator checks if 'f' has a its first argument of the type FrameworkConsole in order to
     return the function with the right arguments.

    If first argument is a FrameworkConsole, args[1] is split as if it were input as a raw_input argument.
     Otherwise, arguments are used normally.

    :param examples: list of usage examples
    :param autocomplete: list of choices to be displayed when typing 2 x <TAB>
    :param behavior: attribute to be associated to the decorated function for handling a particular behavior
    :return: the decorator function
    """
    def decorator(f):
        # set command attributes
        kwargs.setdefault('behavior', DefaultCommand)
        for kw, arg in kwargs.items():
            setattr(f, kw, arg)

        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args[1].split(), **kwargs) \
                    if len(args) > 1 and isinstance(args[0], Cmd) else f(*args, **kwargs)
            except KeyboardInterrupt:
                pass
        return wrapper
    return decorator


# *************************************** PATH-RELATED DECORATORS ****************************************
def expand_file(inside=None, ensure_ext=None):
    """
    This decorator expands the path to the specified filename. If this filename is not already a path,
     expand it to specified folder 'inside'. If an extension is to be ensured, check and add it if relevant.

    :param fn: input filename
    :param inside: folder to expand in order to build filename's path (if not already specified in filename)
    :param ensure_ext: extension to be ensured for the file
    :return: the decorator function
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            fn = args[0]
            if inside and dirname(fn) == '':
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
    :return: the decorator function
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
    This decorator catches f's signature and checks for bad input arguments in order to pretty report
     them in a customized way.

    :param f: the decorated function
    :return: the wrapper with its original arguments or exit with return code 2 if bad arguments
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        sig = signature(f)
        args = () if args == ('',) else args
        # first, exclude variable arguments and keyword-arguments
        novar_args = [p for p in sig.parameters.values() if not str(p).startswith('*')]
        # then, retrieve arguments without default values
        nodef_args = [p for p in novar_args if p.default is not p.empty]
        # now, if less input arguments are provided than the number of arguments without default value, display an error
        if len(args) < len(novar_args) - len(nodef_args):
            logging.critical("Bad input arguments !")
            logging.info("This command has the following signature: {}{}".format(f.__name__, str(sig)))
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
