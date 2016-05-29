#!/usr/bin/env python
# -*- coding: utf-8 -*-
from fabric.api import local, task

from lib.commands import get_commands


@task
def console():
    """ Open framework's console. """
    local('python main.py')


for name, func in get_commands(exclude=['list']):
    globals()[name] = task(func)
