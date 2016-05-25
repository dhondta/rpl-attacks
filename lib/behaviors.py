# -*- coding: utf8 -*-
from datetime import datetime, timedelta

from .constants import TASK_EXPIRATION
from .logconfig import logging


class DefaultCommand(object):
    is_multiprocessed = False


class MultiprocessedCommand(object):
    is_multiprocessed = True

    def __init__(self, console, command, name):
        super(MultiprocessedCommand, self).__init__()
        self.pool = console.pool
        self.tasklist = console.tasklist
        self.command = command
        self.short = '_'.join(command.__name__.split('_')[1:])
        self.name = name
        self.tasklist[self] = {
            'name': name,
            'command': self.short,
            'status': 'INIT',
            'expires': None,
            'result': None,
        }

    def __str__(self):
        return '{}[{}]'.format(self.name, self.short)

    def __set_info(self, status, result=None, expires=True):
        logging.debug(' > Process {} is over.'.format(self))
        self.tasklist[self].update({'status': status, 'result': result})
        if expires:
            self.tasklist[self]['expires'] = datetime.now() + timedelta(seconds=TASK_EXPIRATION)

    def callback(self, result):
        self.__set_info('SUCCESS' if result is not False else 'FAILED', result)

    def error_callback(self, result):
        self.__set_info('FAIL', result)

    def is_expired(self):
        return datetime.now() > (self.tasklist[self]['expires'] or datetime.now())

    def run(self, *args, **kwargs):
        if self not in self.tasklist.keys() or self.tasklist[self]['status'] != 'PENDING':
            self.__set_info('PENDING', expires=False)
            self.pool.apply_async(self.command, args, kwargs,
                                  callback=self.callback, error_callback=self.error_callback)
