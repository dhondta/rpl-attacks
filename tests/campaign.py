#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sh
import unittest
from jsmin import jsmin
from json import loads
from os.path import exists, expanduser, join

from core.commands import drop, prepare
from core.conf.constants import EXPERIMENT_FOLDER


JSON = 'test-campaign.json'


class ExperimentTestCase(unittest.TestCase):
    path = expanduser(join(EXPERIMENT_FOLDER, JSON))
    backup = path + '.backup'


class Test6Prepare(ExperimentTestCase):
    """ 6. Prepare a simulation campaign """

    @classmethod
    def setUpClass(cls):
        if exists(cls.path):
            sh.mv(cls.path, cls.backup)
        prepare(JSON, ask=False, silent=True)

    def test1_campaign_format(self):
        """ > Is the new experiment campaign a correct JSON file ? """
        try:
            with open(self.path) as f:
                loads(jsmin(f.read()))
            passed = True
        except:
            passed = False
        self.assertTrue(passed)


class Test7Drop(ExperimentTestCase):
    """ 7. Drop the same simulation campaign """

    @classmethod
    def setUpClass(cls):
        drop(JSON, ask=False, silent=True)

    @classmethod
    def tearDownClass(cls):
        if exists(cls.backup):
            sh.mv(cls.backup, cls.path)

    def test1_campaign_dropped(self):
        """ > Is the campaign JSON file removed ? """
        self.assertFalse(exists(self.path))
