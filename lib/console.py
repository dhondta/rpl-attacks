# -*- coding: utf-8 -*-
import atexit
import signal
from cmd import Cmd
from copy import copy
from funcsigs import signature
from inspect import getmembers, isfunction
from multiprocessing import Pool, cpu_count
from os import system
from six.moves import zip_longest
from sys import modules
from types import MethodType

from .constants import BANNER, COMMAND_DOCSTRING
from .logconfig import logging, set_logging


class Console(Cmd, object):
    """ Simple command processor with standard commands. """
    file = None
    prompt = ">>> "
    ruler = None

    def default(self, line):
        print(" [!] Unknown command: {}".format(line))

    def do_clear(self, line):
        """
    Clear the screen.
        """
        system("clear")

    def do_exit(self, line):
        """
    Exit the interpreter (also possible with Ctrl-D shortcut).
        """
        return True

    def do_EOF(self, line):
        """
    Exit the interpreter (triggered with Ctrl-D shortcut).
        """
        print("")
        return True


class FrameworkConsole(Console):
    """ Base command processor for the RPL Attacks Framework. """
    intro = "\n{}\nType help or ? to list commands.\nNB: DO NOT use spaces in arguments !\n".format(BANNER)

    def __init__(self, parallel=False):
        self.__last_tasklist = None
        processes = cpu_count()
        self.pool = Pool(processes, lambda: signal.signal(signal.SIGINT, signal.SIG_IGN))
        self.tasklist = {}
        self.reexec = ['status']
        for name, func in [(n, f) for n, f in getmembers(modules['lib.commands'], isfunction) \
                           if hasattr(f, 'behavior')]:
            shortname = func.__name__.split("_")[-1]
            # set the behavior of the console command (multi-processed or not)
            setattr(Console, name, MethodType(FrameworkConsole.start_process_template(func) \
                                              if parallel and func.behavior.is_multiprocessed else func, self))
            # retrieve parts of function's docstring to make console command's docstring
            parts = func.__doc__.split(':param ')
            description = parts[0].strip()
            arguments = [" ".join([l.strip() for l in x.split(":")[-1].split('\n')]) for x in parts[1:]]
            docstring = COMMAND_DOCSTRING["description"].format(description)
            if len(arguments) > 0:
                arg_descrs = [' - {}:\t{}'.format(n, d or "[no description]") \
                              for n, d in list(zip_longest(signature(func).parameters.keys(), arguments or []))]
                docstring += COMMAND_DOCSTRING["arguments"].format('\n'.join(arg_descrs))
            if hasattr(func, 'examples') and isinstance(func.examples, list):
                args_examples = [' >>> {} {}'.format(shortname, e) for e in func.examples]
                docstring += COMMAND_DOCSTRING["examples"].format('\n'.join(args_examples))
            setattr(getattr(getattr(Console, name), '__func__'), '__doc__', docstring)
            # set the autocomplete list of values (can be lazy by using lambda) if relevant
            if hasattr(func, 'autocomplete'):
                setattr(Console, 'complete_{}'.format(shortname),
                        MethodType(FrameworkConsole.complete_template(func.autocomplete), self))
            if hasattr(func, 'reexec_on_emptyline') and func.reexec_on_emptyline:
                self.reexec.append(shortname)
        super(FrameworkConsole, self).__init__()
        atexit.register(self.graceful_exit)

    def __clean_tasks(self):
        """ Private method for cleaning the list of tasks. """
        for t in [x for x in self.tasklist.keys() if x.is_expired()]:
            del self.tasklist[t]

    def do_loglevel(self, line):
        """
    Change the log level (info|warning|error|debug) [default: info].
        """
        if line != '' and set_logging(line):
            print(' [I] Verbose level is now set to: {}'.format(line))

    def do_status(self, line):
        """
    Display process pool status.
        """
        self.__clean_tasks()
        if line == 'restart' and self.__last_tasklist is not None and \
                hash(frozenset(self.tasklist)) == self.__last_tasklist:
            return
        self.__last_tasklist = hash(frozenset(copy(self.tasklist)))
        print(' [I] Status of opened tasks:')
        if len(self.tasklist) == 0:
            print('\tNo task currently')
        else:
            width = max([len(str(t)) for t in self.tasklist.keys()])
            for task, info in sorted(self.tasklist.items(), key=lambda x: x[0]):
                print('\t{}: {}'.format(str(task).ljust(width), info['status']))
        print('')

    def emptyline(self):
        """ Re-execute last command if it's in the list of commands to be re-executed. """
        if self.lastcmd == 'status':
            self.do_status('restart')
        elif self.lastcmd and self.lastcmd.split()[0] in self.reexec:
            return self.onecmd(self.lastcmd)

    def graceful_exit(self):
        """ Exit handler for terminating the process pool gracefully. """
        if 'PENDING' in [x['status'] for x in self.tasklist.values()]:
            logging.info(" > Waiting for opened processes to finish...")
            logging.warning("Hit CTRL+C a second time to force process termination.")
            try:
                self.pool.close()
                self.pool.join()
            except KeyboardInterrupt:
                logging.info(" > Terminating opened processes...")
                self.pool.terminate()
                self.pool.join()

    @staticmethod
    def complete_template(lazy_values):
        """ Template method for handling auto-completion. """
        def _template(self, text, line, start_index, end_index):
            try:
                values = lazy_values()
            except TypeError:
                values = lazy_values or []
            return [v for v in values if v.startswith((text or "").strip())]
        return _template

    @staticmethod
    def start_process_template(f):
        """ Template method for handling multi-processed commands. """
        def _template(self, *args, **kwargs):
            self.__clean_tasks()
            if args == ('',):
                return False
            short = '_'.join(f.__name__.split('_')[1:])
            if not any([i['name'] == args[0] and short == i['command'] for i in self.tasklist.values()]):
                print("")
                f.behavior(self, f, args[0]).run(*args, **kwargs)
                print(self.prompt)
            else:
                logging.warning("A task {}[{}] is already running...".format(args[0], short))
        return _template
