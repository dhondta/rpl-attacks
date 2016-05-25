#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse

from lib import FrameworkConsole


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog=__file__,
                                     description="RPL Attack Framework Console.",
                                     epilog="Usage examples:\n python main.py\n python3 main.py",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-p", dest="parallel", action="store_true", help="parallel mode [default: false]")
    args = parser.parse_args()
    console = FrameworkConsole(args.parallel)
    try:
        console.cmdloop()
    except KeyboardInterrupt:
        print("")
        exit(0)
