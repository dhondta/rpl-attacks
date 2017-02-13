#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sh
import unittest
from os.path import exists, expanduser, join

from core.commands import config, setup, update
from core.conf.constants import COOJA_FOLDER


class Test1Config(unittest.TestCase):
    """ 1. Config file creation """

    config_file = expanduser('~/.rpl-attacks.conf')
    backup = config_file + '.backup'

    @classmethod
    def setUpClass(cls):
        if exists(cls.config_file):
            sh.mv(cls.config_file, cls.backup)
        config(silent=True)

    @classmethod
    def tearDownClass(cls):
        if exists(cls.backup):
            sh.mv(cls.backup, cls.config_file)

    def test1_config_file_is_correctly_formatted(self):
        """ > Is the configuration file correctly formatted ? """
        contiki_folder, experiments_folder = '', ''
        with open(self.config_file) as f:
            for line in f.readlines():
                if line.startswith('contiki_folder'):
                    contiki_folder = line
                elif line.startswith('experiments_folder'):
                    experiments_folder = line
        self.assertIn('contiki_folder = ', contiki_folder)
        self.assertIn('experiments_folder = ', experiments_folder)


class Test2CoojaSetup(unittest.TestCase):
    """ 2. Cooja setup """

    def test1_modify_cooja(self):
        """ > Is Cooja's java source correctly adapted ? """
        with open(join(COOJA_FOLDER, 'java', 'org', 'contikios', 'cooja', 'Cooja.java')) as f:
            for line in f.readlines():
                if '-hidden' in line:
                    break
        self.assertIn('-hidden', line)

    def test2_update_cooja_build(self):
        """ > Is Cooja's build.xml correctly adapted ? """
        assertions, section = {'clean': '', 'jar': ''}, None
        with open(join(COOJA_FOLDER, 'build.xml')) as f:
            for line in f.readlines():
                if '<target name="clean" depends="init">' in line:
                    section = 'clean'
                elif '<target name="jar" depends="jar_cooja">' in line:
                    section = 'jar'
                if section is not None and '"apps/visualizer_screenshot"' in line:
                    assertions[section] = line
        for line in assertions.values():
            self.assertIn('"apps/visualizer_screenshot"', line)

    def test3_update_cooja_user_properties(self):
        """ > Is Cooja's user properties file correctly adapted ? """
        with open(join(expanduser('~'), '.cooja.user.properties')) as f:
            for line in f.readlines():
                if line.startswith('DEFAULT_PROJECTDIRS='):
                    break
        self.assertIn('[APPS_DIR]/visualizer_screenshot', line)

    def test4_visualizer_screenshot_installed(self):
        """ > Is VisualizerScreenshot Cooja plugin installed ? """
        visualizer_folder = join(COOJA_FOLDER, 'apps', 'visualizer_screenshot')
        self.assertTrue(exists(visualizer_folder))
        self.assertTrue(exists(join(visualizer_folder, 'build.xml')))
        self.assertTrue(exists(join(visualizer_folder, 'cooja.config')))
        self.assertTrue(exists(join(visualizer_folder, 'lib', 'visualizer_screenshot.jar')))
        self.assertTrue(exists(join(visualizer_folder, 'java', 'VisualizerScreenshot.java')))
