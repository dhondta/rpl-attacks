# -*- coding: utf8 -*-
import logging


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
    logging.basicConfig(format=' %(levelname)s [%(name)s] (%(filename)s:%(lineno)d) - %(message)s', level=lvl)
    coloredlogs.install(lvl)
    return True
set_logging()


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
