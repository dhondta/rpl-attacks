# -*- coding: utf8 -*-
import logging


# logging configuration
LOG_LEVEL = logging.INFO
logging.basicConfig(format=' %(levelname)s [%(name)s] (%(filename)s:%(lineno)d) - %(message)s', level=LOG_LEVEL)
HIDDEN = ['warnings', 'stdout', 'stderr', 'running']
try:
    import coloredlogs
    coloredlogs.install(logging.DEBUG)
except:
    print("(Install 'coloredlogs' for colored logging)")
logger = logging.getLogger('sh.command')
logger.setLevel(level=logging.WARNING)
logger = logging.getLogger('sh.streamreader')
logger.setLevel(level=logging.WARNING)
logger = logging.getLogger('sh.stream_bufferer')
logger.setLevel(level=logging.WARNING)
