#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import unittest

from lib.constants import COOJA_FOLDER, FRAMEWORK_FOLDER
from lib.install import modify_cooja, update_cooja_build, update_cooja_user_properties


class TestFabSetup(unittest.TestCase):

    def test_modify_cooja(self):
        modify_cooja(COOJA_FOLDER)
        with open(os.path.join(COOJA_FOLDER, 'java', 'org', 'contikios', 'cooja', 'Cooja.java')) as f:
            source = f.read()
        for line in source.split('\n'):
            if '-test' in line:
                break
        self.assertRegex('-test', line)

    def test_update_cooja_build(self):
        update_cooja_build(COOJA_FOLDER)
