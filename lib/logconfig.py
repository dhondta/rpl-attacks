# -*- coding: utf8 -*-
import logging
from sys import stdout

LOG_FORMAT = '%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s'


# colorize logging
try:
    import coloredlogs
    coloredlogs_installed = True
except ImportError:
    coloredlogs_installed = False
    print("(Install 'coloredlogs' for colored logging)")


# logging configuration
def set_logging(lvl='info'):
    try:
        lvl = {
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'debug': logging.DEBUG,
        }[lvl]
    except KeyError:
        return False
    logging.basicConfig(format=LOG_FORMAT, level=lvl)
    coloredlogs.install(lvl, fmt=LOG_FORMAT)
    return True
set_logging()


# Inspired from: http://stackoverflow.com/questions/3118059/how-to-write-custom-python-logging-handler
class ProgressConsoleHandler(logging.StreamHandler):
    """
    A handler to display a progress bar in the bottom of the terminal window
    """
    on_same_line = False

    def __init__(self, width, height):
        self.width, self.height = width, height
        super(ProgressConsoleHandler, self).__init__(self)

    def emit(self, record):
        try:
            ProgressConsoleHandler.print_at(1, self.height - 1, self.format(record))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise

    # Source: http://stackoverflow.com/questions/7392779/is-it-possible-to-print-a-string
    #               -at-a-certain-screen-position-inside-idle
    @staticmethod
    def print_at(x, y, text):
        stdout.write("\x1b7\x1b[%d;%df%s\x1b8" % (x, y, text))
        stdout.flush()


# fabric verbose lists of options
HIDDEN_ALL = ['warnings', 'stdout', 'stderr', 'running']
HIDDEN_KEEP_STDERR = ['warnings', 'stdout', 'running']


# silent sh module's logging
logger = logging.getLogger('sh.command')
logger.setLevel(level=logging.WARNING)
logger = logging.getLogger('sh.streamreader')
logger.setLevel(level=logging.WARNING)
logger = logging.getLogger('sh.stream_bufferer')
logger.setLevel(level=logging.WARNING)


# get application logger
logger = logging.getLogger('rpla')
#logger.addHandler(ProgressConsoleHandler(*get_terminal_size()))
