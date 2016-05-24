#!/usr/bin/env python
# -*- coding: utf-8 -*-
from lib import *


@task
def console():
    FrameworkConsole().cmdloop()


for name in [n for n, o in getmembers(modules[__name__], isfunction) if hasattr(o, 'cmd')]:
    short_name = name.split('_')[-1]
    exec('{}.__name__ = "{}"'.format(name, short_name))
    exec('{} = task({})'.format(short_name, name))
