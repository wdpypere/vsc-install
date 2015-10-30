#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# Copyright 2015-2015 Ghent University
#
# This file is part of vsc-install,
# originally created by the HPC team of Ghent University (http://ugent.be/hpc/en),
# with support of Ghent University (http://ugent.be/hpc),
# the Flemish Supercomputer Centre (VSC) (https://vscentrum.be/nl/en),
# the Hercules foundation (http://www.herculesstichting.be/in_English)
# and the Department of Economy, Science and Innovation (EWI) (http://www.ewi-vlaanderen.be/en).
#
# http://github.com/hpcugent/vsc-install
#
# vsc-install is free software: you can redistribute it and/or modify
# it under the terms of the GNU Library General Public License as
# published by the Free Software Foundation, either version 2 of
# the License, or (at your option) any later version.
#
# vsc-install is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public License
# along with vsc-install. If not, see <http://www.gnu.org/licenses/>.
#
"""
Shared module for vsc software testing

VSCImport usage: make a module 00-import.py in the test/ dir that has only the following line
   from vsc.install.testing import VSCImportTest

Running python setup.py test will pick this up and do its magic

@author: Stijn De Weirdt (Ghent University)
"""
import os
import sys

from unittest import TestCase, TestLoader
from vsc.install.shared_setup import generate_packages, generate_scripts, generate_modules

class VSCImportTest(TestCase):
    """Dummy class to prove importing VSC namespace works"""

    EXTRA_PKGS = None # additional packages to test / try to import
    EXCLUDE_PKGS = None # list of regexp patters to remove from list of package to test

    EXTRA_MODS = None # additional modules to test / try to import
    EXCLUDE_MODS = None # list of regexp patterns to remove from list of modules to test

    EXTRA_SCRIPTS = None # additional scripts to test / try to import
    EXCLUDE_SCRIPTS = None # list of regexp patterns to remove from list of scripts to test

    def _import(self, pkg):
        try:
            __import__(pkg)
        except ImportError:
            pass

        self.assertTrue(pkg in sys.modules, msg='import %s was success' % pkg)

    def test_import_packages(self):
        """Try to import each namespace"""
        for pkg in generate_packages(extra=self.EXTRA_PKGS, exclude=self.EXCLUDE_PKGS):
            self._import(pkg)

    def test_import_modules(self):
        """Try to import each module"""
        for modname in generate_modules(extra=self.EXTRA_MODS, exclude=self.EXCLUDE_MODS):
            self._import(modname)

    def test_importscripts(self):
        """Try to import each python script as a module"""
        # sys.path is already setup correctly
        for scr in generate_scripts(extra=self.EXTRA_SCRIPTS, exclude=self.EXCLUDE_SCRIPTS):
            if not scr.endswith('.py'):
                continue
            self._import(os.path.basename(scr)[:-len('.py')])
