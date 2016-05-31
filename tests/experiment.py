#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sh
import unittest
from os.path import exists, expanduser, getmtime, join

from lib.commands import clean, make, remake
from lib.constants import EXPERIMENT_FOLDER
from lib.utils import check_structure


SIM = 'test-simulation'


class ExperimentTestCase(unittest.TestCase):
    path = expanduser(join(EXPERIMENT_FOLDER, SIM))
    backup = path + '.backup'


class Test3Make(ExperimentTestCase):

    @classmethod
    def setUpClass(cls):
        if exists(cls.path):
            sh.mv(cls.path, cls.backup)
        make(SIM, ask=False, silent=True)

    def test1_experiment_structure(self):
        """ Is the new experiment correctly structured ? """
        self.assertTrue(check_structure(self.path))


class Test4Remake(ExperimentTestCase):

    @classmethod
    def setUpClass(cls):
        cls.t1 = getmtime(join(cls.path, 'motes', 'malicious.z1'))
        remake(SIM, silent=True)
        cls.t2 = getmtime(join(cls.path, 'motes', 'malicious.z1'))

    def test1_experiment_structure_unchanged(self):
        """ Is the new experiment still correctly structured ? """
        self.assertTrue(check_structure(self.path))

    def test2_malicious_mote_recompiled(self):
        """ Is the malicious mote well recompiled ? """
        self.assertNotEqual(self.t1, self.t2)


class Test5Clean(ExperimentTestCase):

    @classmethod
    def setUpClass(cls):
        clean(SIM, ask=False, silent=True)

    @classmethod
    def tearDownClass(cls):
        if exists(cls.backup):
            sh.mv(cls.backup, cls.path)

    def test1_experiment_cleaned(self):
        """ Is the experiment folder removed ? """
        self.assertFalse(exists(self.path))
