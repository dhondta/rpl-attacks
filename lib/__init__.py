# -*- coding: utf8 -*-
import logging
import os

from collections import OrderedDict
from fabric.api import hide, lcd, local, settings, task

from .analyze import dashboard
from .constants import CONTIKI_FOLDER, COOJA_FOLDER, EXPERIMENT_FOLDER, TEMPLATES_FOLDER, TEMPLATE_ENV, \
                       MAX_XY_POSITION, MIN_DIST_BETWEEN_MOTES, MAX_DIST_BETWEEN_MOTES, NBR_MOTES
from .helpers import copy_files, copy_folder, move_folder, remove_files, remove_folder, render_templates
from .install import modify_cooja, update_cooja_build, update_cooja_user_properties
from .logconfig import HIDDEN
from .parser import powertracker2csv, pcap2csv
from .utils import get_experiments, get_path
