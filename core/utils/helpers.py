# -*- coding: utf8 -*-
import ast
from os.path import join
from six import string_types

from core.conf.logconfig import logger


__all__ = [
    'read_config',
    'write_config',
]


# *********************************** SIMULATION CONFIG HELPERS *************************************
def read_config(path, sep=' = '):
    """
    This helper function reads a simple configuration file with the following format:

     max_range = 50.0
     repeat    = 1
     blocks    = []
     goal      = ""
     ...

    :param path: path to the configuration file
    :param sep: separator between the key and the value
    :return: dictionary with the whole configuration
    """
    config = {}
    try:
        with open(join(path, 'simulation.conf')) as f:
            for line in f.readlines():
                if line.strip().startswith('#'):
                    continue
                try:
                    k, v = [x.strip() for x in line.split(sep)]
                except ValueError:
                    continue
                try:
                    v = ast.literal_eval(v)
                except ValueError:
                    pass
                config[k] = v
    except OSError:
        logger.error("Configuration file 'simulation.conf' does not exist !")
    return config


def write_config(path, config, sep=' = '):
    """
    This helper function saves a simple configuration file.

    :param path: path to the configuration file
    :param config: dictionary with the whole configuration
    :param sep: separator between the key and the value
    """
    width = max([len(k) for k in config.keys()])
    with open(join(path, 'simulation.conf'), 'w') as f:
        for k, v in sorted(config.items(), key=lambda x: x[0]):
            f.write('{}{}{}\n'.format(k.ljust(width), sep, ['{}', '"{}"'][isinstance(v, string_types)].format(v)))
