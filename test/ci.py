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
import os
import shutil
import tempfile

from vsc.install.ci import gen_jenkinsfile, gen_tox_ini
from vsc.install.testing import TestCase


class CITest(TestCase):
    """License related tests"""

    def setUp(self):
        """Test setup"""
        super(CITest, self).setUp()

        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        """Test cleanup"""
        shutil.rmtree(self.tmpdir)

        super(CITest, self).tearDown()

    def test_gen_jenkinsfile(self):
        """Test generating of Jenkinsfile."""
        os.chdir(self.tmpdir)
        gen_jenkinsfile()

        self.assertTrue(os.path.exists('Jenkinsfile'))

        error_pattern = r"File .*/%s/Jenkinsfile already exists" % os.path.basename(self.tmpdir)
        error_pattern += ", use --force to overwrite"
        self.assertErrorRegex(OSError, error_pattern, gen_jenkinsfile)

        gen_jenkinsfile(force=True)

    def test_tox_ini(self):
        """Test generating of Jenkinsfile."""
        os.chdir(self.tmpdir)
        gen_tox_ini()

        self.assertTrue(os.path.exists('tox.ini'))

        # overwriting requires force
        error_pattern = r"File .*/%s/tox.ini already exists" % os.path.basename(self.tmpdir)
        error_pattern += ", use --force to overwrite"
        self.assertErrorRegex(OSError, error_pattern, gen_tox_ini)

        gen_tox_ini(force=True)
