# -*- coding: utf8 -*-
import dill
import os
import signal
import time
from datetime import datetime, timedelta
from multiprocessing import TimeoutError

from core.conf.constants import TASK_EXPIRATION
from core.conf.logconfig import logger


__all__ = [
    'DefaultCommand',
    'MultiprocessedCommand',
]


class DefaultCommand(object):
    """
    This is the default class for indicating that a command is sequentially executed
    """
    is_multiprocessed = False

    def __init__(self, console, command, name, path=None):
        super(DefaultCommand, self).__init__()
        self.tasklist = console.tasklist
        self.command = command
        self.name = name
        self.pids = ['{}/with{}-malicious/.{}'.format(path, x, command.__name__.lstrip('_')) for x in ["out", ""]] \
                    if path is not None else []

    def run(self, *args, **kwargs):
        return self.command(*args, **kwargs)


class MultiprocessedCommand(DefaultCommand):
    """
    This class handles command multi-processing and is to be attached to a console through its constructor's
     arguments.
    """
    is_multiprocessed = True

    def __init__(self, console, command, name, path):
        super(MultiprocessedCommand, self).__init__(console, command, name, path)
        self.pool = console.pool
        self.task = None
        self.tasklist[self] = {
            'name': name,
            'command': self.command.__name__,
            'status': 'INIT',
            'expires': None,
            'result': 'Not defined yet',
        }

    def __str__(self):
        return '{}[{}]'.format(self.name, self.command.__name__.lstrip('_'))

    def __set_info(self, status, result=None, expires=True):
        if status != 'PENDING':
            logger.debug(' > Process {} is over.'.format(self))
        self.tasklist[self].update({'status': status, 'result': result or self.tasklist[self]['result']})
        if expires:
            self.tasklist[self]['expires'] = datetime.now() + timedelta(seconds=TASK_EXPIRATION)

    def callback(self, state):
        if isinstance(state, tuple):
            self.__set_info(*state)
        else:
            self.__set_info('UNDEFINED', "None")

    def is_expired(self):
        return datetime.now() > (self.tasklist[self]['expires'] or datetime.now())

    def kill(self, retries=3, pause=.1):
        try:
            try:
                self.task.get(1)
                self.__set_info('KILLED', "None")
            except (AttributeError, TimeoutError):
                self.__set_info('CANCELLED', "None")
            except UnicodeEncodeError:
                self.__set_info('CRASHED', "None")
            for pid in self.pids:
                try:
                    with open(pid) as f:
                        os.kill(int(f.read().strip()), signal.SIGTERM)
                    os.remove(pid)
                except (IOError, OSError):
                    pass  # simply fail silently when no PID or OS cannot kill it as it is already terminated
            if self.command.__name__.lstrip('_') == 'run' and retries > 0:
                time.sleep(pause)  # wait ... sec that the next call from the command starts
                                   # this is necessary e.g. with cooja command (when Cooja starts a first time for
                                   #  a simulation without a malicious mote then a second time with)
                self.kill(retries - 1, 2 * pause)  # then kill it
        except KeyboardInterrupt:
            self.kill(0, 0)

    def run(self, *args, **kwargs):
        if self not in self.tasklist.keys() or self.tasklist[self]['status'] != 'PENDING':
            self.__set_info('PENDING', expires=False)
            kwargs.pop('console', None)  # console instance must be removed as it is unpickable and will thus make
            #                               apply_async fail
            kwargs['loglevel'] = logger.level  # logging level is appended to set it in the subprocess
            self.task = self.pool.apply_async(self.command, args, kwargs, callback=self.callback)
