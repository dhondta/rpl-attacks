# -*- coding: utf8 -*-
import logging

from fabric.api import hide, lcd, local, settings, task
from os.path import dirname, exists, expanduser, join

from .analyze import dashboard
from .constants import CONTIKI_FOLDER, COOJA_FOLDER, EXPERIMENT_FOLDER, FRAMEWORK_FOLDER, TEMPLATES_FOLDER, \
                       TEMPLATE_ENV, MIN_DIST_BETWEEN_MOTES, MAX_DIST_BETWEEN_MOTES
from .helpers import copy_files, copy_folder, expand_file, move_folder, remove_files, remove_folder
from .install import modify_cooja, update_cooja_build, update_cooja_user_properties
from .logconfig import HIDDEN_ALL, HIDDEN_KEEP_STDERR
from .parser import powertracker2csv, pcap2csv
from .utils import get_experiments, get_path, render_templates, validated_parameters

reuse_bin_path = None
