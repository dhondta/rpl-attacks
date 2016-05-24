# -*- coding: utf8 -*-
from funcsigs import signature
from functools import wraps
from os.path import dirname, join
from six.moves import zip_longest

from .console import FrameworkConsole
from .constants import COMMAND_DOCSTRING
from .logconfig import logging


# ************************************* GENERIC COMMAND DECORATORS **************************************
def command(examples=None, autocomplete=None):
    """
    This decorator checks if 'f' has a its first argument of the type FrameworkConsole in order to
     return the function with the right arguments.

    If first argument is a FrameworkConsole, args[1] is split as if it were input as a raw_input argument.
     Otherwise, arguments are used normally.

    :param description: command description
    :param arguments: list of command argument descriptions
    :param examples: list of usage examples
    :param autocomplete: list of choices to be displayed when typing 2 x <TAB>
    :return: the decorator function
    """
    def decorator(f):
        f.cmd = True
        shortname = f.__name__.split("_")[-1]
        parts = f.__doc__.split(':param ')
        description = parts[0].strip()
        arguments = [" ".join([l.strip() for l in x.split(":")[-1].split('\n')]) for x in parts[1:]]
        arg_descrs = [' - {}:\t{}'.format(n, d or "[no description]") \
                      for n, d in list(zip_longest(signature(f).parameters.keys(), arguments or []))]
        args_examples = [' >>> {} {}'.format(shortname, e) for e in (examples or [])]
        if arguments is None and examples is None:
            f.doc = "\n{}\n".format(description)
        else:
            f.doc = COMMAND_DOCSTRING \
                .format(description, '\n'.join(arg_descrs), '\n'.join(args_examples or []))
        if autocomplete is not None:
            setattr(f, 'complete_{}'.format(shortname), FrameworkConsole.complete_template(autocomplete))

        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args[1].split(), **kwargs) \
                    if len(args) > 1 and isinstance(args[0], FrameworkConsole) else f(*args, **kwargs)
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
