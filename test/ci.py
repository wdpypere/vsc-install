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
import os
import re
import shutil
import sys
import tempfile

try:
    from cStringIO import StringIO  # Python 2
except ImportError:
    from io import StringIO  # Python 3

import vsc.install.ci
from vsc.install.ci import JENKINSFILE_REVISION, TOX_INI_REVISION, gen_jenkinsfile, gen_tox_ini, write_file
from vsc.install.testing import TestCase


def read_file(path):
    """Read file at specified path, and return contents."""
    with open(path, 'r') as handle:
        return handle.read()


class CITest(TestCase):
    """License related tests"""

    def setUp(self):
        """Test setup"""
        super(CITest, self).setUp()

        self.cwd = os.getcwd()
        self.tmpdir = tempfile.mkdtemp()
        self.tmpdir_name = os.path.basename(self.tmpdir)

    def tearDown(self):
        """Test cleanup"""
        shutil.rmtree(self.tmpdir)
        os.chdir(self.cwd)

        super(CITest, self).tearDown()

    def run_function(self, function, *args, **kwargs):
        """Run specified function with specified arguments, and capture generated stdout/stderr."""
        orig_handlers = vsc.install.ci.LOG.handlers[:]
        stringio = StringIO()
        handler = logging.StreamHandler(stringio)
        vsc.install.ci.LOG.handlers = [handler]

        function(*args, **kwargs)

        stdout = stringio.getvalue()
        vsc.install.ci.LOG.handlers = orig_handlers

        return stdout

    def test_gen_jenkinsfile(self):
        """Test generating of Jenkinsfile."""

        for pkg in ['vsc-install', 'vsc-base']:
            testdir = os.path.join(self.tmpdir, pkg)
            os.makedirs(testdir)
            os.chdir(testdir)

            def check_stdout(stdout):
                """Helper function to check stdout output."""
                self.assertTrue(stdout.startswith('[Jenkinsfile]'))
                regex = re.compile(r"^Wrote .*/%s/%s/Jenkinsfile$" % (self.tmpdir_name, pkg), re.M)
                self.assertTrue(regex.search(stdout), "Pattern '%s' found in: %s" % (regex.pattern, stdout))

            check_stdout(self.run_function(gen_jenkinsfile))
            self.assertTrue(os.path.exists('Jenkinsfile'))

            expected = [
                "// Jenkinsfile: scripted Jenkins pipefile",
                "// [revision: %s]" % JENKINSFILE_REVISION,
                "// This file was automatically generated using 'python -c vsc.install.ci -f'",
                "// DO NOT EDIT MANUALLY",
                '',
                "node {",
                "    stage 'checkout git'",
                "    checkout scm",
                "    stage 'test'",
                "    sh 'python2.7 -V'",
                "    sh 'tox -v'",
                '}',
            ]
            expected = '\n'.join(expected)

            self.assertEqual(read_file('Jenkinsfile'), expected)

            error_pattern = r"File .*/%s/%s/Jenkinsfile already exists" % (self.tmpdir_name, pkg)
            error_pattern += ", use --force to overwrite"
            # could be either IOError or OSError, depending on the Python version being used, so check for Exception
            self.assertErrorRegex(Exception, error_pattern, self.run_function, gen_jenkinsfile)

            # overwrite existing tox.ini, so we can check contents after re-generating it
            write_file('Jenkinsfile', "This is not a valid Jenkinsfile file", force=True)

            check_stdout(self.run_function(gen_jenkinsfile, force=True))
            self.assertEqual(read_file('Jenkinsfile'), expected)

    def test_tox_ini(self):
        """Test generating of tox.ini."""

        for pkg in ['vsc-install', 'vsc-base']:
            testdir = os.path.join(self.tmpdir, pkg)
            os.makedirs(testdir)
            os.chdir(testdir)

            def check_stdout(stdout):
                """Helper function to check stdout output."""
                self.assertTrue(stdout.startswith('[tox.ini]'))
                regex = re.compile(r"^Wrote .*/%s/%s/tox\.ini$" % (self.tmpdir_name, pkg), re.M)
                self.assertTrue(regex.search(stdout), "Pattern '%s' found in: %s" % (regex.pattern, stdout))

            check_stdout(self.run_function(gen_tox_ini))
            self.assertTrue(os.path.exists('tox.ini'))

            expected = [
                "# tox.ini: configuration file for tox",
                "# [revision: %s]" % TOX_INI_REVISION,
                "# This file was automatically generated using 'python -c vsc.install.ci -f'",
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
            expected = '\n'.join(expected)

            self.assertEqual(read_file('tox.ini'), expected)

            # overwriting requires force
            error_pattern = r"File .*/%s/%s/tox.ini already exists" % (self.tmpdir_name, pkg)
            error_pattern += ", use --force to overwrite"
            # could be either IOError or OSError, depending on the Python version being used, so check for Exception
            self.assertErrorRegex(Exception, error_pattern, self.run_function, gen_tox_ini)

            # overwrite existing tox.ini, so we can check contents after re-generating it
            write_file('tox.ini', "This is not a valid tox.ini file", force=True)

            check_stdout(self.run_function(gen_tox_ini, force=True))
            self.assertEqual(read_file('tox.ini'), expected)
