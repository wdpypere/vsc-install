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
from vsc.install.ci import gen_jenkinsfile, gen_tox_ini, write_file
from vsc.install.testing import TestCase


class CITest(TestCase):
    """License related tests"""

    def setUp(self):
        """Test setup"""
        super(CITest, self).setUp()

        self.tmpdir = tempfile.mkdtemp()
        self.tmpdir_name = os.path.basename(self.tmpdir)

    def tearDown(self):
        """Test cleanup"""
        shutil.rmtree(self.tmpdir)

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
        os.chdir(self.tmpdir)

        def check_stdout(stdout):
            """Helper function to check stdout output."""
            self.assertTrue(stdout.startswith('[Jenkinsfile]'))
            regex = re.compile(r"^Wrote .*/%s/Jenkinsfile$" % self.tmpdir_name, re.M)
            self.assertTrue(regex.search(stdout), "Pattern '%s' found in: %s" % (regex.pattern, stdout))

        check_stdout(self.run_function(gen_jenkinsfile))
        self.assertTrue(os.path.exists('Jenkinsfile'))

        error_pattern = r"File .*/%s/Jenkinsfile already exists" % os.path.basename(self.tmpdir)
        error_pattern += ", use --force to overwrite"
        # could be either IOError or OSError, depending on the Python version being used, so check for Exception
        self.assertErrorRegex(Exception, error_pattern, self.run_function, gen_jenkinsfile)

        # overwrite existing tox.ini, so we can check contents after re-generating it
        fake_txt = "This is not a valid Jenkinsfile file"
        write_file('Jenkinsfile', fake_txt, force=True)

        check_stdout(self.run_function(gen_jenkinsfile, force=True))
        with open('Jenkinsfile') as fp:
            txt = fp.read()
        self.assertTrue(txt != fake_txt)

    def test_tox_ini(self):
        """Test generating of tox.ini."""
        os.chdir(self.tmpdir)

        def check_stdout(stdout):
            """Helper function to check stdout output."""
            self.assertTrue(stdout.startswith('[tox.ini]'))
            regex = re.compile(r"^Wrote .*/%s/tox\.ini$" % self.tmpdir_name, re.M)
            self.assertTrue(regex.search(stdout), "Pattern '%s' found in: %s" % (regex.pattern, stdout))

        check_stdout(self.run_function(gen_tox_ini))
        self.assertTrue(os.path.exists('tox.ini'))

        # overwriting requires force
        error_pattern = r"File .*/%s/tox.ini already exists" % self.tmpdir_name
        error_pattern += ", use --force to overwrite"
        # could be either IOError or OSError, depending on the Python version being used, so check for Exception
        self.assertErrorRegex(Exception, error_pattern, self.run_function, gen_tox_ini)

        # overwrite existing tox.ini, so we can check contents after re-generating it
        fake_txt = "This is not a valid tox.ini file"
        write_file('tox.ini', fake_txt, force=True)

        check_stdout(self.run_function(gen_tox_ini, force=True))
        with open('tox.ini') as fp:
            txt = fp.read()
        self.assertTrue(txt != fake_txt)
