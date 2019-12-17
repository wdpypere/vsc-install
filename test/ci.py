#
# Copyright 2019-2019 Ghent University
#
# This file is part of vsc-install,
# originally created by the HPC team of Ghent University (http://ugent.be/hpc/en),
# with support of Ghent University (http://ugent.be/hpc),
# the Flemish Supercomputer Centre (VSC) (https://www.vscentrum.be),
# the Flemish Research Foundation (FWO) (http://www.fwo.be/en)
# and the Department of Economy, Science and Innovation (EWI) (http://www.ewi-vlaanderen.be/en).
#
# https://github.com/hpcugent/vsc-install
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
Test CI functionality

@author: Kenneth Hoste (Ghent University)
"""
import logging
import mock
import os
import re
import shutil
import sys
import tempfile

from vsc.install.ci import gen_jenkinsfile, gen_tox_ini
from vsc.install.testing import TestCase


class CITest(TestCase):
    """License related tests"""

    def test_gen_jenkinsfile(self):
        """Test generating of Jenkinsfile."""

        for pkg in ['vsc-install', 'vsc-base']:
            expected = [
                "// Jenkinsfile: scripted Jenkins pipefile",
                "// This file was automatically generated using 'python -m vsc.install.ci'",
                "// DO NOT EDIT MANUALLY",
                '',
                "node {",
                "    stage 'checkout git'",
                "    checkout scm",
                "    stage 'test'",
                "    sh 'python2.7 -V'",
                "    sh 'python -m easy_install -U --user tox'",
                "    sh 'export PATH=$HOME/.local/bin:$PATH && tox -v'",
                '}',
            ]
            expected = '\n'.join(expected) + '\n'

            self.assertEqual(gen_jenkinsfile(), expected)

    def test_tox_ini(self):
        """Test generating of tox.ini."""

        for pkg in ['vsc-install', 'vsc-base']:

            expected = [
                "# tox.ini: configuration file for tox",
                "# This file was automatically generated using 'python -m vsc.install.ci'",
                "# DO NOT EDIT MANUALLY",
                '',
                "[tox]",
                "envlist = py27,py36",
                "skipsdist = true",
                "skip_missing_interpreters = true",
                '',
                "[testenv]",
            ]

            if pkg != 'vsc-install':
                expected.append("commands_pre = python -m easy_install -U vsc-install")

            expected.extend([
                "commands = python setup.py test",
                '',
                "[testenv:py36]",
                "ignore_outcome = true",
            ])
            expected = '\n'.join(expected) + '\n'

            self.assertEqual(gen_tox_ini(pkg), expected)
