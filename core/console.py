# -*- coding: utf-8 -*-
import atexit
import os
from copy import copy
from funcsigs import signature
from getpass import getuser
from multiprocessing import cpu_count, Pool
from signal import signal, SIGINT, SIG_IGN, SIGTERM
from six.moves import zip_longest
from socket import gethostname
from subprocess import check_output, Popen, PIPE
from sys import stdout
from termcolor import colored
from terminaltables import SingleTable
from types import MethodType

from core import *
from core.commands import get_commands


class FrameworkConsole(Console):
    """ Base command processor for the RPL Attacks Framework. """
    banner = BANNER
    pidfile = PIDFILE
    prompt = surround_ansi_escapes('{}{}{}{}{}{} '.format(
        colored(getuser(), 'magenta'),
        colored('@', 'cyan'),
        colored(gethostname(), 'blue'),
        colored(':', 'cyan'),
        colored('rpl-attacks', 'red'),
        colored('>>', 'cyan'),
    ))
    welcome = "\nType help or ? to list commands.\n"

    def __init__(self, parallel):
        self.continuation_prompt = self.prompt
        self.parallel = parallel
        width, height = get_terminal_size() or MIN_TERM_SIZE
        if any(map((lambda s: s[0] < s[1]), zip((height, width), MIN_TERM_SIZE))):
            stdout.write("\x1b[8;{rows};{cols}t".format(rows=max(MIN_TERM_SIZE[0], height),
                                                        cols=max(MIN_TERM_SIZE[1], width)))
        if self.parallel:
            processes = cpu_count()
            self.__last_tasklist = None
            self.tasklist = {}
            self.pool = Pool(processes, lambda: signal(SIGINT, SIG_IGN))
        atexit.register(self.graceful_exit)
        self.reexec = ['status']
        self.__bind_commands()
        super(FrameworkConsole, self).__init__()
        self.do_loglevel('info')
        self.do_clear('')

    def __bind_commands(self):
        if not self.parallel:
            for attr in ['complete_kill', 'do_kill', 'do_status']:
                delattr(FrameworkConsole, attr)
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
                              for n, d in list(zip_longest(signature(func).parameters.keys(), arguments or [])) if n is not None]
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

    def clean_tasks(self):
        """ Method for cleaning the list of tasks. """
        for t in [x for x in self.tasklist.keys() if x.is_expired()]:
            del self.tasklist[t]

    def cmdloop(self, intro=None):
        if hasattr(self, "already_running") and self.already_running:
            with open(self.pidfile) as f:
                pid = f.read().strip()
            logger.warn('RPL Attacks Framework is already running in another terminal (PID: {})'.format(pid))
            self.graceful_exit()
        else:
            super(FrameworkConsole, self).cmdloop()

    def complete_kill(self, text, *args):
        return sorted([str(i) for i in self.tasklist.keys() if str(i).startswith(text) \
            and i.tasklist[i]['status'] == "PENDING"])

    def complete_loglevel(self, text, *args):
        return sorted([str(i) for i in LOG_LEVELS.keys() if str(i).startswith(text)])

    def do_kill(self, task):
        """
    Kill a task from the pool.
        """
        matching = [t for t in self.tasklist.keys() if str(t) == task and self.tasklist[t]['status'] == 'PENDING']
        if len(matching) > 0:
            matching[0].kill()
        else:
            print(' [!] Task {} does not exist or is not a pending task'.format(task))

    def do_loglevel(self, level):
        """
    Change the log level (info|warning|error|debug) [default: info].
        """
        if level in LOG_LEVELS.keys() and set_logging(level):
            print(' [I] Verbose level is now set to: {}'.format(level))
        else:
            print(' [!] Unknown verbose level: {}'.format(level))

    @no_arg_command_except('restart')
    def do_status(self, line):
        """
    Display process pool status.
        """
        self.clean_tasks()
        # this prevents from re-displaying the same status table once ENTER is pressed
        #  (marker 'restart' is handled in emptyline() hereafter
        if line == 'restart' and self.__last_tasklist is not None and \
                        hash(repr(self.tasklist)) == self.__last_tasklist:
            return
        self.__last_tasklist = hash(repr(copy(self.tasklist)))
        if len(self.tasklist) == 0:
            data = [['No task currently running']]
        else:
            data = [['Task', 'Status', 'Result']]
            for task, info in sorted(self.tasklist.items(), key=lambda x: str(x[0])):
                data.append([str(task).ljust(15), info['status'].ljust(10), str(info['result']).ljust(40)])
        table = SingleTable(data, 'Status of opened tasks')
        table.justify_columns = {0: 'center', 1: 'center', 2: 'center'}
        print(table.table)

    def emptyline(self):
        """ Re-execute last command if it's in the list of commands to be re-executed. """
        try:
            lastcmd = self.lastcmd.split()[0]
        except IndexError:
            return
        if lastcmd in self.reexec:
            if lastcmd == 'status':
                self.lastcmd = 'status restart'
            return self.onecmd(self.lastcmd)

    def graceful_exit(self):
        """ Exit handler for terminating the process pool gracefully. """
        try:
            os.remove(self.pidfile)
        except:
            pass
        if hasattr(self, "tasklist") and 'PENDING' in [x['status'] for x in self.tasklist.values()]:
            logger.info(" > Waiting for opened processes to finish...")
            logger.warning("Hit CTRL+C a second time to force process termination.")
            try:
                for task_obj in self.tasklist.keys():
                    # see: http://stackoverflow.com/questions/1408356/keyboard-interrupts-with-pythons-multiprocessing-pool
                    #  "The KeyboardInterrupt exception won't be delivered until wait() returns, and it never returns,
                    #   so the interrupt never happens. KeyboardInterrupt should almost certainly interrupt a condition
                    #   wait. Note that this doesn't happen if a timeout is specified; cond.wait(1) will receive the
                    #   interrupt immediately. So, a workaround is to specify a timeout."
                    task_obj.task.get(999999)
                self.pool.close()
                #self.pool.join()
            except KeyboardInterrupt:
                logger.info(" > Terminating opened processes...")
                for task_obj in self.tasklist.keys():
                    task_obj.kill()
                self.pool.terminate()
                self.pool.join()

    def task_pending(self, name):
        return self.parallel and any([i['name'] == name and i['status'] == 'PENDING' for i in self.tasklist.values()])

    def wait_for_task(self, name):
        """ Wait for pending tasks with the given name until finished. """
        while self.task_pending(name):
            sleep(.1)

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
