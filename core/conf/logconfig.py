# -*- coding: utf8 -*-
import logging
# colorize logging
try:
    import coloredlogs
except ImportError:
    coloredlogs = None
    print("(Install 'coloredlogs' for colored logging)")


__all__ = [
    'logger',
    'set_logging',
    'LOG_LEVELS',
    'HIDDEN_ALL',
    'HIDDEN_KEEP_STDERR',
]


LOG_FORMAT = '%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s'
LOG_LEVELS = {
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'debug': logging.DEBUG,
}


# logging configuration
logger = None
def set_logging(lvl='info'):
    global logger
    try:
        if not (isinstance(lvl, int) and lvl in LOG_LEVELS.values()):
            lvl = LOG_LEVELS[lvl]
    except KeyError:
        return False
    logging.basicConfig(format=LOG_FORMAT, level=lvl)
    if coloredlogs is not None:
        coloredlogs.install(lvl, fmt=LOG_FORMAT)
    if logger is not None:
        logger.setLevel(lvl)
    return True
set_logging()
# this avoids throwing e.g. FutureWarning or DeprecationWarning messages
logging.captureWarnings(True)
logger = logging.getLogger('py.warnings')
logger.setLevel(logging.CRITICAL)


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
