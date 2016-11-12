# -*- coding: utf8 -*-
import dill
from datetime import datetime, timedelta

from core.conf.constants import TASK_EXPIRATION
from core.conf.logconfig import logger


class DefaultCommand(object):
    """
    This is the default class for indicating that a command is sequentially executed
    """
    is_multiprocessed = False

    def __init__(self, console, command, name):
        super(DefaultCommand, self).__init__()
        self.tasklist = console.tasklist
        self.command = command
        self.name = name

    def run(self, *args, **kwargs):
        return self.command(*args, **kwargs)


class MultiprocessedCommand(DefaultCommand):
    """
    This class handles command multi-processing and is to be attached to a console through its constructor's
     arguments.
    """
    is_multiprocessed = True

    def __init__(self, console, command, name):
        super(MultiprocessedCommand, self).__init__(console, command, name)
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

    def callback(self, result):
        if isinstance(result, tuple):
            self.__set_info(*result)
        else:
            self.__set_info('UNDEFINED')

    def cancelled(self):
        self.__set_info('CANCELLED')

    def crashed(self):
        self.__set_info('CRASHED')

    def is_expired(self):
        return datetime.now() > (self.tasklist[self]['expires'] or datetime.now())

    def run(self, *args, **kwargs):
        if self not in self.tasklist.keys() or self.tasklist[self]['status'] != 'PENDING':
            self.__set_info('PENDING', expires=False)
            kwargs.pop('console', None)  # console instance must be removed as it is unpickable and will thus make
            #                               apply_async fail
            kwargs['loglevel'] = logger.level  # logging level is appended to set it in the subprocess
            self.task = self.pool.apply_async(self.command, args, kwargs, callback=self.callback)
