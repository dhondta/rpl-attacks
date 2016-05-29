#!/usr/bin/env python
# -*- coding: utf-8 -*-
from os import system

from lib.console import FrameworkConsole


if __name__ == '__main__':
    system('clear')
    cli = FrameworkConsole(parallel=True,
                           disabled=['@@', 'ed', 'hi', 'l', 'li', 'pause', 'q', 'r',
                                     'cmdenvironment', 'save', '_load', '_relative_load'])
    cli.cmdloop()
