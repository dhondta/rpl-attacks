# -*- coding: utf8 -*-
from cmd import Cmd
from funcsigs import signature
from functools import update_wrapper, wraps
from os.path import exists, expanduser, join

from .behaviors import DefaultCommand, MultiprocessedCommand
from .helpers import std_input
from .lexer import ArgumentsLexer
from .logconfig import logger


lexer = ArgumentsLexer()


# ************************************* GENERIC COMMAND DECORATORS **************************************
def command(**params):
    """
    This decorator checks if 'f' has a its first argument of the type FrameworkConsole in order to
     return the function with the right arguments.

    If first argument is a FrameworkConsole, args[1] is split as if it were input as a raw_input argument.
     Otherwise, arguments are used normally.

    :param examples: list of usage examples
    :param autocomplete: list of choices to be displayed when typing 2 x <TAB>
    :param behavior: attribute to be associated to the decorated function for handling a particular behavior
    :param not_exists: specifies a tuple (argument_name, error_message[, ])
    :param exists:
    :param start_msg: message to be displayed before calling 'f'
    :param reexec_on_emptyline: boolean indicating if the command is to be reexecuted when an empty line is
                                 input in the console
    :param add_console_to_kwargs: boolean indicating if the 'console' object is to be added to kwargs
                                   (for usage inside command's code)
    :param __base__: special parameter to be used if the command is to be multi-processed, it holds the
                      "monitored" version of the command (that is, encapsulated inside a try-except)
    :return: the decorator function
    """
    def decorator(f):
        # set command attributes
        params.setdefault('behavior', DefaultCommand)
        params.setdefault('add_console_to_kwargs', False)
        for key, val in params.items():
            setattr(f, key, val)

        @wraps(f)
        def wrapper(*args, **kwargs):
            # specific argument existence check through the 'not_exists' and 'exists' attributes
            def get_ask(sig, attrs):
                if attrs['on_boolean'] in kwargs.keys():
                    return kwargs[attrs['on_boolean']]
                try:
                    param = sig.parameters[attrs['on_boolean']]
                    try:
                        return args[list(sig.parameters.values()).index(param)]
                    except (IndexError, ValueError):  # occurs if 'ask' was not specified in the arguments ;
                        #                                in this case, take the default value from the signature
                        return param.default
                except KeyError:  # occurs if no 'ask' parameter is in the signature
                    return False

            # log message formatting with specified arguments from 'args' or 'kwargs'
            def log_msg(lvl, msg):
                if kwargs.get('silent'):
                    return
                if isinstance(msg, tuple):
                    values = []
                    for arg in msg[1:]:
                        try:
                            values.append(args[list(sig.parameters.keys()).index(arg)])
                        except KeyError:
                            value = kwargs.get(arg)
                            if value is not None:
                                values.append(value)
                    getattr(logger, lvl)(msg[0].format(*values))
                else:
                    getattr(logger, lvl)(msg)

            console = args[0] if len(args) > 0 and isinstance(args[0], Cmd) else None
            if console is not None and f.add_console_to_kwargs:
                kwargs['console'] = console
            # lexical analysis
            if len(args) > 1 and console is not None:
                line = args[1]
                kwargs_tmp = {k: v for k, v in kwargs.items()}
                args, kwargs = lexer.analyze(line)
                if args is None and kwargs is None:
                    print(console.badcmd_msg.format("Invalid", '{} {}'.format(f.__name__, line)))
                    return
                kwargs.update(kwargs_tmp)
            # bad signature check
            sig = signature(f)
            args = () if args == ('',) else args     # occurs in case of Cmd ; an empty 'line' can be passed if a
            #                                           command is called without any argument
            # - first, exclude variable arguments and keyword-arguments
            no_var_args = [p for p in list(sig.parameters.values()) if not str(p).startswith('*')]
            # - then, retrieve arguments without default values
            no_def_args = [p for p in no_var_args if p.default is not p.empty]
            # - now, if less input arguments are provided than the number of arguments without default value,
            #    display an error
            if len(args) < len(no_var_args) - len(no_def_args):
                logger.critical("Bad input arguments !")
                logger.info("This command has the following signature: {}{}".format(f.__name__, str(sig)))
                logger.info("Please check the documentation for more information.")
                return
            # expand a specified argument to a path
            if hasattr(f, 'expand'):
                arg, attrs = f.expand
                arg_idx = list(sig.parameters.keys()).index(arg)
                try:
                    expanded = expanduser(join(attrs['into'], args[arg_idx]))
                except IndexError:  # occurs when arg_idx out of range of args, meaning that the argument to be
                    #                  expanded was not provided
                    return
                if attrs.get('ext') and not expanded.endswith("." + attrs['ext']):
                    expanded += "." + attrs['ext']
                if attrs.get('new_arg') is None:
                    args = tuple([a if i != arg_idx else expanded for i, a in enumerate(args)])
                elif attrs['new_arg'] not in list(sig.parameters.keys()):
                    kwargs[attrs['new_arg']] = expanded if attrs.get('apply') is None else attrs['apply'](expanded)
            # check for existence (or not) and ask for a confirmation to continue if required
            for fattr in ['exists', 'not_exists']:
                if hasattr(f, fattr):
                    arg, attrs = getattr(f, fattr)
                    try:
                        arg_val = args[list(sig.parameters.keys()).index(arg)]
                    except ValueError:
                        arg_val = kwargs[arg]
                    if (fattr == 'exists' and exists(arg_val)) or (fattr == 'not_exists' and not exists(arg_val)):
                        if 'loglvl' in attrs.keys() and 'msg' in attrs.keys():
                            log_msg(attrs['loglvl'], attrs['msg'])
                        if attrs.get('loglvl') in ('error', 'critical') or \
                                ((attrs.get('loglvl') in ('warning', 'info') or fattr == 'exists') and
                                 get_ask(sig, attrs) and attrs.get('confirm') is not None and
                                 not std_input(attrs['confirm'], 'yellow') == 'yes'):
                            return
            # run the command and catch exception if any
            if f.behavior is MultiprocessedCommand and console is not None:
                console.clean_tasks()
                if not any([i['name'] == args[0] and i['status'] == 'PENDING' for i in console.tasklist.values()]):
                    if hasattr(f, 'start_msg'):
                        log_msg('info', f.start_msg)
                    f.behavior(console, f.__base__, args[0]).run(*args, **kwargs)
                else:
                    logger.warning("A task is still pending on this experiment ({})"
                                   .format(f.__base__.__name__.lstrip('_')))
            else:
                if hasattr(f, 'start_msg'):
                    log_msg('info', f.start_msg)
                f(*args, **kwargs)
        return wrapper
    return decorator


class CommandMonitor(object):
    """
    This ugly class decorator is aimed to make a function 'f' pickable (required for multiprocessing) while
     using a decoration handling exceptions and returning a tuple ([status], [result/error message]).

    :param f: the decorated function
    """
    def __init__(self, f):
        self.f = f
        try:
            update_wrapper(self, f)
        except:
            pass

    def __call__(self, *args, **kwargs):
        try:
            return 'SUCCESS', self.f(*args, **kwargs) or 'No result'
        except Exception as e:
            return 'FAIL', '{}: {}'.format(e.__class__.__name__, str(e))


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
            logger.critical("Command '{}' returned error code {} with the following error:\n"
                            .format(cmd, out.return_code) + '\n'.join(filtered))
            return
    return wrapper
