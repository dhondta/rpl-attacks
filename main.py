#!/usr/bin/env python
# -*- coding: utf-8 -*-
from lib import FrameworkConsole


if __name__ == '__main__':
    try:
        FrameworkConsole().cmdloop()
    except KeyboardInterrupt:
        print("")
        exit(0)
