# -*- coding: utf8 -*-
from fabric.api import task
from inspect import getmembers, isfunction
from sys import modules

from .commands import \
    do_clean, \
    do_config, \
    do_cooja, \
    do_make, \
    do_make_all, \
    do_prepare, \
    do_remake, \
    do_rip_my_slip, \
    do_run, \
    do_run_all, \
    do_setup, \
    do_test
from .console import FrameworkConsole
