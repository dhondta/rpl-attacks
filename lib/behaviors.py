# -*- coding: utf8 -*-
import dill
from datetime import datetime, timedelta

from .constants import TASK_EXPIRATION
from .logconfig import logger


class DefaultCommand(object):
    """
    This is the default class for indicating that a command is sequentially executed
    """
    is_multiprocessed = False


class MultiprocessedCommand(object):
    """
    This class handles command multi-processing and is to be attached to a console through its constructor's
     arguments.
    """
    is_multiprocessed = True

    def __init__(self, console, command, name):
        super(MultiprocessedCommand, self).__init__()
        self.pool = console.pool
        self.tasklist = console.tasklist
        self.command = command
        self.name = name
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
        logger.debug(' > Process {} is over.'.format(self))
        self.tasklist[self].update({'status': status, 'result': result or self.tasklist[self]['result']})
        if expires:
            self.tasklist[self]['expires'] = datetime.now() + timedelta(seconds=TASK_EXPIRATION)

    def callback(self, result):
        if isinstance(result, tuple):
            self.__set_info(*result)
        else:
            self.__set_info('UNDEFINED')

    def is_expired(self):
        return datetime.now() > (self.tasklist[self]['expires'] or datetime.now())

    def run(self, *args, **kwargs):
        if self not in self.tasklist.keys() or self.tasklist[self]['status'] != 'PENDING':
            self.__set_info('PENDING', expires=False)
            kwargs.pop('console', None)  # console instance must be removed as it is unpickable and will thus make
            #                               apply_async fail
            self.task = self.pool.apply_async(self.command, args, kwargs, callback=self.callback)
