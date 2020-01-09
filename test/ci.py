#
# Copyright 2019-2020 Ghent University
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

from vsc.install.ci import TOX_INI, gen_jenkinsfile, gen_tox_ini, parse_vsc_ci_cfg
from vsc.install.testing import TestCase


JENKINSFILE_INIT = """// Jenkinsfile: scripted Jenkins pipefile
// This file was automatically generated using 'python -m vsc.install.ci'
// DO NOT EDIT MANUALLY

node {
    stage('checkout git') {
        checkout scm
        // remove untracked files (*.pyc for example)
        sh 'git clean -fxd'
    }
"""

JENKINSFILE_TEST_STAGE = """    stage('test') {
        sh 'python2.7 -V'
        sh 'python -m easy_install -U --user tox'
        sh 'export PATH=$HOME/.local/bin:$PATH && tox -v -c %s'
    }
""" % TOX_INI


EXPECTED_JENKINSFILE_DEFAULT = JENKINSFILE_INIT + JENKINSFILE_TEST_STAGE + '}\n'

EXPECTED_JENKINSFILE_JIRA = JENKINSFILE_INIT + JENKINSFILE_TEST_STAGE + """    stage('PR title JIRA link') {
        if (env.CHANGE_ID) {
            if (env.CHANGE_TITLE =~ /\s+\(?HPC-\d+\)?$/) {
                echo "title ${env.CHANGE_TITLE} seems to contain JIRA ticket number."
            } else {
                echo "ERROR: title ${env.CHANGE_TITLE} does not end in 'HPC-number'."
                error("malformed PR title ${env.CHANGE_TITLE}.")
            }
        }
    }
}
"""

JENKINSFILE_SHELLCHECK_STAGE = """    stage ('shellcheck') {
        sh 'curl --silent https://storage.googleapis.com/shellcheck/shellcheck-latest.linux.x86_64.tar.xz --output - | tar -xJv'
        sh 'cp shellcheck-latest/shellcheck .'
        sh 'rm -r shellcheck-latest'
        sh './shellcheck --version'
        sh './shellcheck bin/*.sh'
    }
"""

EXPECTED_JENKINSFILE_SHELLCHECK = JENKINSFILE_INIT + JENKINSFILE_SHELLCHECK_STAGE + JENKINSFILE_TEST_STAGE + '}\n'

EXPECTED_TOX_INI = """# tox.ini: configuration file for tox
# This file was automatically generated using 'python -m vsc.install.ci'
# DO NOT EDIT MANUALLY

[tox]
envlist = py27,py36
skipsdist = true
skip_missing_interpreters = true

[testenv]
commands_pre =
    pip install 'setuptools<42.0'
    python -m easy_install -U vsc-install
commands = python setup.py test
passenv = USER

[testenv:py36]
ignore_outcome = true
"""


class CITest(TestCase):
    """License related tests"""

    def setUp(self):
        """Test setup."""
        super(CITest, self).setUp()

        os.chdir(self.tmpdir)

    def write_vsc_ci_ini(self, txt):
        """Write vsc-ci.ini file in current directory with specified contents."""
        fh = open('vsc-ci.ini', 'w')
        fh.write('[vsc-ci]\n')
        fh.write(txt)
        fh.write('\n')
        fh.close()

    def test_parse_vsc_ci_cfg(self):
        """Test parse_vsc_ci_cfg function."""

        # (basically) empty vsc-ci.ini
        self.write_vsc_ci_ini('')
        expected = {
            'jira_issue_id_in_pr_title': False,
            'run_shellcheck': False,
        }
        self.assertEqual(parse_vsc_ci_cfg(), expected)

        # vsc-ci.ini with unknown keys is trouble
        self.write_vsc_ci_ini("unknown_key=1")
        error_msg = "Unknown key in vsc-ci.ini: unknown_key"
        self.assertErrorRegex(ValueError, error_msg, parse_vsc_ci_cfg)

        self.write_vsc_ci_ini('\n'.join([
            'jira_issue_id_in_pr_title=1',
            'run_shellcheck=true',
        ]))
        expected = {
            'jira_issue_id_in_pr_title': True,
            'run_shellcheck': True,
        }
        self.assertEqual(parse_vsc_ci_cfg(), expected)

    def test_gen_jenkinsfile(self):
        """Test generating of Jenkinsfile."""
        self.assertEqual(gen_jenkinsfile(), EXPECTED_JENKINSFILE_DEFAULT)

    def test_gen_jenkinsfile_jira_issue_id_in_pr_title(self):
        """Test generating of Jenkinsfile incl. check for JIRA issue in PR title."""

        self.write_vsc_ci_ini('jira_issue_id_in_pr_title=1')

        jenkinsfile_txt = gen_jenkinsfile()
        self.assertEqual(jenkinsfile_txt, EXPECTED_JENKINSFILE_JIRA)

    def test_gen_jenkinsfile_shellcheck(self):
        """Test generating of Jenkinsfile incl. running of shellcheck."""

        self.write_vsc_ci_ini('run_shellcheck=1')
        jenkinsfile_txt = gen_jenkinsfile()
        self.assertEqual(jenkinsfile_txt, EXPECTED_JENKINSFILE_SHELLCHECK)

    def test_tox_ini(self):
        """Test generating of tox.ini."""
        self.assertEqual(gen_tox_ini(), EXPECTED_TOX_INI)
