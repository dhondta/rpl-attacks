# -*- coding: utf8 -*-
import logging


# logging configuration
LOG_LEVEL = logging.INFO
logging.basicConfig(format=' %(levelname)s [%(name)s] (%(filename)s:%(lineno)d) - %(message)s', level=LOG_LEVEL)

# fabric verbose lists of options
HIDDEN_ALL = ['warnings', 'stdout', 'stderr', 'running']
HIDDEN_KEEP_STDERR = ['warnings', 'stdout', 'running']

# colorize logging
try:
    import coloredlogs
    coloredlogs.install(logging.DEBUG)
except ImportError:
    print("(Install 'coloredlogs' for colored logging)")

# silent sh module's logging
logger = logging.getLogger('sh.command')
logger.setLevel(level=logging.WARNING)
logger = logging.getLogger('sh.streamreader')
logger.setLevel(level=logging.WARNING)
logger = logging.getLogger('sh.stream_bufferer')
logger.setLevel(level=logging.WARNING)
