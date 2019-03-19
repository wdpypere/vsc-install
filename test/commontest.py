#
# Copyright 2016-2019 Ghent University
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
"""Test commontest"""

import glob
import os

from vsc.install import commontest
from vsc.install.shared_setup import log, vsc_setup
from vsc.install.testing import TestCase


class commontestTest(TestCase):
    """Test commontest """

    def setUp(self):
        """create a self.setup.instance for every test"""
        super(commontestTest, self).setUp()
        self.setup = vsc_setup()

    def test_prospecrtorfail(self):
        """Test that whitelisted warnings actually fails"""
        if not HAS_PROSPECTOR and sys.version_info >= (2, 7) and 'JENKINS_URL' in os.environ:
            # This is fatal on jenkins/...
            self.assertTrue(False, 'prospector must be installed in jenkins environment')

        base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'commontest')
        test_files = glob.glob(os.path.join(base_dir, 'lib', 'vsc', 'mockinstall', "*.py"))
        test_files = [ x for x in test_files if not '__init__.py' in x]
        log.debug("test_files = %s" % test_files) 
        log.debug("base_dir = %s" % base_dir)
        
        # For some reason, prospector does not check files if the path is given (probably becasue it contains "test"),
        # even if ignore_patterns are cleraed. (so we give the individual files)
        # prospector = commontest.run_prospector(base_dir, clear_ignore_patterns = True)
        prospector = commontest.run_prospector(test_files, clear_ignore_patterns = True)
        log.debug("prospector profile from prospector = %s" % prospector.config.profile.__dict__)
        
        failures = []
        for testfile in test_files:
            testfile_base = os.path.basename(testfile)[:-3].replace("_", "-")
            if testfile_base not in commontest.PROSPECTOR_WHITELIST:
                log.warn("'%s' is not in PROSPECTOR_WHITELIST" % testfile_base)

            testfile_report = []
            for msg in prospector.get_messages():
                log.debug("prospector messages %s" % msg.as_dict())
                if msg.location.path == testfile:
                    testfile_report.extend([msg.code, msg.message])

            log.debug("testfile_report = %s" % testfile_report)
            if testfile_base not in testfile_report:
                failures.append(testfile_base)
            else:
                log.info("prospector successfully detected '%s'" % testfile_base)
        
        self.assertFalse(failures, "\nprospector did not detect %s" % failures)
