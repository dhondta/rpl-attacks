#!/usr/bin/env python
# -*- coding: utf-8 -*-
from fabric.api import local, settings, task

from core.commands import get_commands


@task
def console():
    """ Open framework's console. """
    with settings(remote_interrupt=False):
        local('python main.py')


for name, func in get_commands(exclude=['list']):
    globals()[name] = task(func)
