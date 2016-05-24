# -*- coding: utf-8 -*-
from __future__ import absolute_import
from cmd import Cmd
from inspect import getmembers, isfunction
from os import system
from sys import modules
from types import MethodType

from .constants import BANNER
from .logconfig import set_logging


class Console(Cmd, object):
    """ Simple command processor with standard commands. """
    file = None
    prompt = ">>> "
    ruler = None

    def default(self, line):
        print(" [!] Unknown command: {}".format(line))

    def do_clear(self, line):
        """ clear
            Clear the screen """
        system("clear")

    def do_exit(self, line):
        """ exit
            Exit the interpreter (also possible with Ctrl-D shortcut) """
        return True

    def do_EOF(self, line):
        """ EOF
            Exit the interpreter (triggered with Ctrl-D shortcut) """
        print("")
        return True


class FrameworkConsole(Console):
    """ Base command processor for the RPL Attacks Framework. """
    intro = "\n{}\nType help or ? to list commands.\nNB: DO NOT use spaces in arguments !\n".format(BANNER)

    def __init__(self):
        for n, o in [(n, o) for n, o in getmembers(modules['lib.commands'], isfunction) if hasattr(o, 'cmd')]:
            exec('Console.{} = MethodType(o, self)'.format(n))
            exec('Console.{}.__func__.__doc__ = o.doc'.format(n))
            shortname = n.split('_')[-1]
            if hasattr(o, 'complete_{}'.format(shortname)):
                exec('Console.complete_{} = MethodType(o.complete_{}, self)'.format(shortname, shortname))
        super(FrameworkConsole, self).__init__()

    def do_loglevel(self, line):
        """ loglevel
            Change the log level (info|warning|error|debug) [default: info] """
        set_logging(line.strip())

    @staticmethod
    def complete_template(lazy_values):
        def _template(self, text, line, start_index, end_index):
            try:
                values = lazy_values()
            except TypeError:
                values = lazy_values
            return [v for v in values if v.startswith((text or "").strip())]
        return _template
