# -*- coding: utf8 -*-
from cmd import Cmd
from funcsigs import signature
from functools import update_wrapper, wraps
from os import system
from os.path import dirname, exists, expanduser, join
from re import match
from time import gmtime, strftime

from core.common.helpers import make_crash_report, std_input
from core.common.lexer import ArgumentsLexer
from core.conf.constants import CRASH_REPORT_DATA
from core.conf.logconfig import logger
from core.utils.behaviors import DefaultCommand, MultiprocessedCommand


__all__ = [
    'command',
    'no_arg_command',
    'no_arg_command_except',
    'stderr',
    'CommandMonitor',
]


lexer = ArgumentsLexer()


# ************************************* GENERIC COMMAND DECORATORS **************************************
def command(**params):
    """
    This decorator checks if 'f' has a its first argument of the type FrameworkConsole in order to
     return the function with the right arguments.

    If first argument is a FrameworkConsole, args[1] is split as if it were input as from raw_input/input.
     Otherwise, arguments are used normally.

    :param params: keyword-arguments defining extended functionalities around the decorated function
                    (see docstring in commands.py for more details about parameters)
    :return: the decorator function
    """
    def decorator(f):
        # set command attributes using decorator's keyword-arguments
        params.setdefault('behavior', DefaultCommand)      # gives a non-multi-processed behavior by default
        for key, val in params.items():
            setattr(f, key, val)

        @wraps(f)
        def wrapper(*args, **kwargs):
            """
            This is the wrapper for the 'command' decorator, handling the following execution flow :
             - It first determines if this command is used with a console
             - In case of console, it performs a lexical analysis
             - Anyway, it performs a signature checking
             - It handles 'expand' parameter
             - It then handles 'exists' and 'not_exists' (in this order)
             - It finally selects the right behavior using 'behavior'
            """
            # specific argument existence check through the 'not_exists' and 'exists' attributes
            def get_ask():
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
                    for a in msg[1:]:
                        try:
                            values.append(args[list(sig.parameters.keys()).index(a)])
                        except KeyError:
                            value = kwargs.get(a)
                            if value is not None:
                                values.append(value)
                    getattr(logger, lvl)(msg[0].format(*values))
                else:
                    getattr(logger, lvl)(msg)

            console = args[0] if len(args) > 0 and isinstance(args[0], Cmd) else None
            if console is not None:
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
                logger.info("This command has the following signature: {}{}"
                            .format(f.__name__, str(sig).replace(', **kwargs', '')))
                logger.info("Please check the documentation for more information.")
                return
            # expand a specified argument to a path
            if hasattr(f, 'expand'):
                arg, attrs = f.expand
                arg_idx = list(sig.parameters.keys()).index(arg)
                try:
                    expanded = expanduser(join(attrs['into'], args[arg_idx]))
                except IndexError:  # occurs when arg_idx out of range of args, meaning that the argument to be
                                    #  expanded was not provided
                    return
                # if an extension was provided and the file path does not end with it, just append it
                if attrs.get('ext') and not expanded.endswith("." + attrs['ext']):
                    expanded += "." + attrs['ext']
                # the expanded argument must not be saved to a new argument name, just replace its old value
                if attrs.get('new_arg') is None:
                    args = tuple([a if i != arg_idx else expanded for i, a in enumerate(args)])
                # otherwise, create the new argument if the name is not used yet
                elif attrs['new_arg'] not in list(sig.parameters.keys()):
                    kwargs[attrs['new_arg']] = expanded if attrs.get('apply') is None else attrs['apply'](expanded)
                # when no 'path' kwarg is set, it must be added based on the direcotory name of the expanded arg
                if 'path' not in kwargs.keys():
                    kwargs['path'] = dirname(expanded)
            # if next commands require sudo, prompt now for privilege elevation
            if getattr(f, 'requires_sudo', False):
                system('sudo ls > /dev/null')
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
                                 get_ask() and attrs.get('confirm') is not None and
                                 not std_input(attrs['confirm'], 'yellow') == 'yes'):
                            return
            # run the command and catch exception if any
            if console is not None and len(args) > 0 and console.parallel:
                console.clean_tasks()
                pending_tasks = {i['name']: str(o) for o, i in console.tasklist.items() if i['status'] == 'PENDING'}
                if args[0] not in pending_tasks.keys():
                    if hasattr(f, 'start_msg'):
                        log_msg('info', f.start_msg)
                    kwargs['task'] = f.__name__.lstrip('_')
                    f.behavior(console, f.__base__ if f.behavior is MultiprocessedCommand else f, args[0],
                        kwargs.get('path')).run(*args, **kwargs)
                else:
                    logger.warning("A task is still pending on this experiment ({})".format(pending_tasks[args[0]]))
            else:
                if hasattr(f, 'start_msg'):
                    log_msg('info', f.start_msg)
                f(*args, **kwargs)
        return wrapper
    return decorator


class CommandMonitor(object):
    """
    This ugly class decorator is aimed to make a function 'f' pickable (required for multiprocessing) while
     using a decoration that handles exceptions and returns a tuple ([status], [result/error message]).

    :param f: the decorated function
    """
    def __init__(self, f, rpt_data=CRASH_REPORT_DATA):
        self.f = f
        self.rpt_data = rpt_data
        try:
            update_wrapper(self, f)
        except:
            pass

    def __call__(self, *args, **kwargs):
        try:
            return 'SUCCESS', self.f(*args, **kwargs) or 'No result'
        except Exception as e:
            i = {"Class": e.__class__.__name__,
                 "At time": strftime("%Y-%m-%d %H:%M:%S", gmtime()),
                 "For task": "{}[{}]".format(args[0], kwargs.get('task'))}
            make_crash_report(i, *self.rpt_data)
            return 'FAIL', '{}: {}'.format(e.__class__.__name__, str(e))


def no_arg_command(f):
    """
    This small decorator is aimed to invalidate some badly formatted console commands, accepted by the base
     Cmd class' methods as these do not handler special characters. E.g. 'clear$erlgihsevg' makes 'clear' apply.

    :param f: the decorated console method
    """
    @wraps(f)
    def wrapper(console, line):
        if line != '':
            console.default(console.lastcmd)
        else:
            return f(console, line)
    return wrapper


def no_arg_command_except(*words):
    """
    This small decorator does the same as the previous one, but handling exception words.
     E.g. we want 'status restart' to work while any other argument is wrong.

    :param f: the decorated console method
    """
    def decorator(f):
        @wraps(f)
        def wrapper(console, line):
            if line != '' and match(r'^({})$'.format('|'.join(words)), line) is None:
                console.default(console.lastcmd)
            else:
                return f(console, line)
        return wrapper
    return decorator


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
        if f.__name__ == 'local':
            kwargs['capture'] = True
        out = f(cmd + ' 2>&1 /dev/null', *args, **kwargs)
        if out is not None and out.return_code != 0:
            filtered = []
            for line in out.split('\n'):
                if any([line.startswith(s) for s in ['cp ', 'mkdir ', '  CC', '  AR']]) or 'warning' in line:
                    continue
                filtered.append(line)
            logger.critical("Command '{}' returned error code {} with the following error:\n"
                            .format(cmd, out.return_code) + '\n'.join(filtered))
            raise Exception("Command '{}' failed.".format(cmd))
    return wrapper
