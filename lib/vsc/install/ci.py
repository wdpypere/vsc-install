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
Generate configuration files for running CI tests.

Run with: python -m vsc.install.ci

@author: Kenneth Hoste (Ghent University)
"""
import logging
import os


JENKINSFILE = 'Jenkinsfile'
TOX_INI = 'tox.ini'

logging.basicConfig(format="%(message)s", level=logging.INFO)


def write_file(path, txt):
    """Write specified contents to specified path."""
    try:
        with open(path, 'w') as handle:
            handle.write(txt)
        logging.info("Wrote %s", path)
    except (IOError, OSError) as err:
        raise IOError("Failed to write %s: %s" % (path, err))


def gen_tox_ini():
    """
    Generate tox.ini configuration file for tox
    see also https://tox.readthedocs.io/en/latest/config.html
    """
    logging.info('[%s]', TOX_INI)

    header = [
        "%s: configuration file for tox" % TOX_INI,
        "This file was automatically generated using 'python -m vsc.install.ci'",
        "DO NOT EDIT MANUALLY",
    ]
    header = ['# ' + l for l in header]

    py3_env = 'py36'
    envs = ['py27', py3_env]

    lines = header + [
        '',
        "[tox]",
        "envlist = %s" % ','.join(envs),
        # instruct tox not to run sdist prior to installing the package in the tox environment
        # (setup.py requires vsc-install, which is not installed yet when 'python setup.py sdist' is run)
        "skipsdist = true",
        # ignore failures due to missing Python version
        # python2.7 must always be available though, see Jenkinsfile
        "skip_missing_interpreters = true",
        '',
        '[testenv]',
        # use easy_install rather than pip to install vsc-install dependency
        # (vsc-* packages may not work when installed with pip due to use of namespace package vsc.*)
        'commands_pre = python -m easy_install -U vsc-install',
        "commands = python setup.py test",
        # $USER is not defined in tox environment, so pass it
        # see https://tox.readthedocs.io/en/latest/example/basic.html#passing-down-environment-variables
        'passenv = USER',
        '',
        # allow failing tests in Python 3, for now...
        '[testenv:%s]' % py3_env,
        "ignore_outcome = true"
    ]

    return '\n'.join(lines) + '\n'


def gen_jenkinsfile():
    """
    Generate Jenkinsfile (in Groovy syntax),
    see also https://jenkins.io/doc/book/pipeline/syntax/#scripted-pipeline
    """
    logging.info('[%s]', JENKINSFILE)

    def indent(line, level=1):
        """Indent string value with level*4 spaces."""
        return ' ' * 4 * level + line

    test_cmds = [
        # make very sure Python 2.7 is available,
        # since we've configured tox to ignore failures due to missing Python interpreters
        # (see skip_missing_interpreters in gen_tox_ini)
        'python2.7 -V',
        'python -m easy_install -U --user tox',
        # make sure 'tox' command installed with --user is available via $PATH
        'export PATH=$HOME/.local/bin:$PATH && tox -v',
    ]

    header = [
        "%s: scripted Jenkins pipefile" % JENKINSFILE,
        "This file was automatically generated using 'python -m vsc.install.ci'",
        "DO NOT EDIT MANUALLY",
    ]
    header = ['// ' + l for l in header]

    lines = header + [
        '',
        "node {",
        indent("stage('checkout git') {"),
        indent("checkout scm", level=2),
        indent('}'),
        indent("stage('test') {"),
    ]
    lines.extend([indent("sh '%s'" % c, level=2) for c in test_cmds] + [
        indent('}'),
        '}',
    ])

    return '\n'.join(lines) + '\n'


def main():
    """Main function: re-generate tox.ini and Jenkinsfile (in current directory)."""

    cwd = os.getcwd()

    tox_ini = os.path.join(cwd, TOX_INI)
    tox_ini_txt = gen_tox_ini()
    write_file(tox_ini, tox_ini_txt)

    jenkinsfile = os.path.join(cwd, JENKINSFILE)
    jenkinsfile_txt = gen_jenkinsfile()
    write_file(jenkinsfile, jenkinsfile_txt)


if __name__ == '__main__':
    main()
