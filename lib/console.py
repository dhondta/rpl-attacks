# -*- coding: utf-8 -*-
import atexit
import dill
import os
import signal
from cmd2 import Cmd
from copy import copy
from funcsigs import signature
from getpass import getuser
from multiprocessing import Pool, cpu_count
from six.moves import zip_longest
from socket import gethostname
from sys import stdout
from termcolor import colored, cprint
from terminaltables import SingleTable
from types import MethodType

from .commands import get_commands
from .constants import BANNER, COMMAND_DOCSTRING, MIN_TERM_SIZE
from .logconfig import logger, set_logging
from .terminalsize import get_terminal_size


class Console(Cmd, object):
    """ Simple command processor with standard commands. """
    file = None
    ruler = None
    badcmd_msg = " [!] {} command: {}"

    def __init__(self, *args, **kwargs):
        super(Console, self).__init__(*args, **kwargs)

    def default(self, line):
        print(self.badcmd_msg.format(["Unknown", "Invalid"][len(line.split()) > 1], line))

    def do_clear(self, line):
        """
    Clear the screen.
        """
        os.system("clear")
        cprint(BANNER, 'cyan', 'on_grey')
        print(self.intro)


class FrameworkConsole(Console):
    """ Base command processor for the RPL Attacks Framework. """
    intro = "\nType help or ? to list commands.\nNB: DO NOT use spaces in arguments !\n"
    prompt = '{}{}{}{}{}{} '.format(
        colored(getuser(), 'magenta', attrs=['underline']),
        colored('@', 'cyan'),
        colored(gethostname(), 'blue'),
        colored(':', 'cyan'),
        colored('rpl-attacks', 'red', attrs=['bold']),
        colored('>>', 'cyan'),
    )
    abbrev = False

    def __init__(self, parallel, disabled=None):
        self.parallel = parallel
        width, height = get_terminal_size()
        if any(map((lambda s: s[0] < s[1]), zip((height, width), MIN_TERM_SIZE))):
            stdout.write("\x1b[8;{rows};{cols}t".format(rows=max(MIN_TERM_SIZE[0], height),
                                                        cols=max(MIN_TERM_SIZE[1], width)))
        if self.parallel:
            processes = cpu_count()
            self.__last_tasklist = None
            self.tasklist = {}
            self.pool = Pool(processes, lambda: signal.signal(signal.SIGINT, signal.SIG_IGN))
            atexit.register(self.graceful_exit)
        self.reexec = ['status']
        self.__bind_commands()
        cprint(BANNER, 'cyan', 'on_grey')
        for shortcut in disabled or []:
            try:
                delattr(Cmd, 'do_' + shortcut)
            except AttributeError:
                shortcut in self.shortcuts.pop(shortcut)
        super(FrameworkConsole, self).__init__()

    def __bind_commands(self):
        if self.parallel:
            self.do_status = self.__do_status
        for name, func in get_commands():
            longname = 'do_{}'.format(name)
            # set the behavior of the console command (multi-processed or not)
            # setattr(Console, longname, MethodType(FrameworkConsole.start_process_template(func) \
            #                                   if self.parallel and func.behavior.is_multiprocessed else func, self))
            setattr(Console, longname, MethodType(func, self))
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
                args_examples = [' >>> {} {}'.format(name, e) for e in func.examples]
                docstring += COMMAND_DOCSTRING["examples"].format('\n'.join(args_examples))
            setattr(getattr(getattr(Console, longname), '__func__'), '__doc__', docstring)
            # set the autocomplete list of values (can be lazy by using lambda) if relevant
            if hasattr(func, 'autocomplete'):
                setattr(Console, 'complete_{}'.format(name),
                        MethodType(FrameworkConsole.complete_template(func.autocomplete), self))
            if hasattr(func, 'reexec_on_emptyline') and func.reexec_on_emptyline:
                self.reexec.append(name)

    def __do_status(self, line):
        """
    Display process pool status.
        """
        self.clean_tasks()
        # this prevents from re-displaying the same status table once ENTER is pressed
        #  (marker 'restart' is handled in emptyline() hereafter
        if line == 'restart' and self.__last_tasklist is not None and \
                hash(frozenset(self.tasklist)) == self.__last_tasklist:
            return
        self.__last_tasklist = hash(frozenset(copy(self.tasklist)))
        if len(self.tasklist) == 0:
            data = [['No task currently running']]
        else:
            data = [['Task', 'Status', 'Result']]
            for task, info in sorted(self.tasklist.items(), key=lambda x: str(x[0])):
                data.append([str(task).ljust(15), info['status'].ljust(10), str(info['result']).ljust(40)])
        table = SingleTable(data, 'Status of opened tasks')
        table.justify_columns = {0: 'center', 1: 'center', 2: 'center'}
        print(table.table)

    def clean_tasks(self):
        """ Method for cleaning the list of tasks. """
        for t in [x for x in self.tasklist.keys() if x.is_expired()]:
            del self.tasklist[t]

    def complete_loglevel(self):
        return ['debug', 'error', 'info', 'warning']

    def do_loglevel(self, line):
        """
    Change the log level (info|warning|error|debug) [default: info].
        """
        if line != '' and set_logging(line):
            print(' [I] Verbose level is now set to: {}'.format(line))

    def emptyline(self):
        """ Re-execute last command if it's in the list of commands to be re-executed. """
        if self.lastcmd == 'status':
            self.do_status('restart')
        elif self.lastcmd and self.lastcmd.split()[0] in self.reexec:
            return self.onecmd(self.lastcmd)

    def graceful_exit(self):
        """ Exit handler for terminating the process pool gracefully. """
        if 'PENDING' in [x['status'] for x in self.tasklist.values()]:
            logger.info(" > Waiting for opened processes to finish...")
            logger.warning("Hit CTRL+C a second time to force process termination.")
            try:
                self.pool.close()
                self.pool.join()
            except KeyboardInterrupt:
                logger.info(" > Terminating opened processes...")
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

    # @staticmethod
    # def start_process_template(f):
    #     """ Template method for handling multi-processed commands. """
    #     def _template(self, *args, **kwargs):
    #         self.__clean_tasks()
    #         if args == ('',):
    #             return False
    #         if not any([i['name'] == args[0] for i in self.tasklist.values()]):
    #             f.behavior(self, f, args[0]).run(*args, **kwargs)
    #         else:
    #             logger.warning("A task {}[{}] is still pending on this experiment...".format(args[0], f.__name__))
    #     return _template
