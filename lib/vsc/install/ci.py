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
Generate configuration files for running CI tests.

Run with: python -m vsc.install.ci

@author: Kenneth Hoste (Ghent University)
"""
import logging
import os
import sys

try:
    # Python 3
    import configparser
except ImportError:
    # Python 2
    import ConfigParser as configparser

from vsc.install.shared_setup import MAX_SETUPTOOLS_VERSION


JENKINSFILE = 'Jenkinsfile'
TOX_INI = 'tox.ini'

VSC_CI = 'vsc-ci'
VSC_CI_INI = VSC_CI + '.ini'

INSTALL_SCRIPTS_PREFIX_OVERRIDE = 'install_scripts_prefix_override'
JIRA_ISSUE_ID_IN_PR_TITLE = 'jira_issue_id_in_pr_title'
RUN_SHELLCHECK = 'run_shellcheck'

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

    vsc_ci_cfg = parse_vsc_ci_cfg()

    if vsc_ci_cfg[INSTALL_SCRIPTS_PREFIX_OVERRIDE]:
        pip_args = '--install-option="--install-scripts={envdir}/bin" '
        easy_install_args = '--script-dir={envdir}/bin '
    else:
        pip_args = ''
        easy_install_args = ''

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
        "commands_pre =",
        # install required setuptools version;
        # we need a setuptools < 42.0 for now, since in 42.0 easy_install was changed to use pip when available;
        # it's important to use pip (not easy_install) here, since only pip will actually remove an older
        # already installed setuptools version
        "    pip install %s'setuptools<%s'" % (pip_args, MAX_SETUPTOOLS_VERSION),
        # install latest vsc-install release from PyPI;
        # we can't use 'pip install' here, because then we end up with a broken installation because
        # vsc/__init__.py is not installed because we're using pkg_resources.declare_namespace
        # (see https://github.com/pypa/pip/issues/1924)
        "    python -m easy_install -U %svsc-install" % easy_install_args,
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


def parse_vsc_ci_cfg():
    """Parse vsc-ci.ini configuration file (if any)."""
    vsc_ci_cfg = {
        INSTALL_SCRIPTS_PREFIX_OVERRIDE: False,
        JIRA_ISSUE_ID_IN_PR_TITLE: False,
        RUN_SHELLCHECK: False,
    }

    if os.path.exists(VSC_CI_INI):
        try:
            cfgparser = configparser.SafeConfigParser()
            cfgparser.read(VSC_CI_INI)
            cfgparser.items(VSC_CI)  # just to make sure vsc-ci section is there
        except (configparser.NoSectionError, configparser.ParsingError) as err:
            logging.error("ERROR: Failed to parse %s: %s" % (VSC_CI_INI, err))
            sys.exit(1)

        # every entry in the vsc-ci section is expected to be a known setting
        for key, _ in cfgparser.items(VSC_CI):
            if key in vsc_ci_cfg:
                vsc_ci_cfg[key] = cfgparser.getboolean(VSC_CI, key)
            else:
                raise ValueError("Unknown key in %s: %s" % (VSC_CI_INI, key))

    return vsc_ci_cfg


def gen_jenkinsfile():
    """
    Generate Jenkinsfile (in Groovy syntax),
    see also https://jenkins.io/doc/book/pipeline/syntax/#scripted-pipeline
    """
    logging.info('[%s]', JENKINSFILE)

    def indent(line, level=1):
        """Indent string value with level*4 spaces."""
        return ' ' * 4 * level + line

    vsc_ci_cfg = parse_vsc_ci_cfg()

    test_cmds = [
        # make very sure Python 2.7 is available,
        # since we've configured tox to ignore failures due to missing Python interpreters
        # (see skip_missing_interpreters in gen_tox_ini)
        'python2.7 -V',
        'python -m easy_install -U --user tox',
        # make sure 'tox' command installed with --user is available via $PATH
        'export PATH=$HOME/.local/bin:$PATH && tox -v -c %s' % TOX_INI,
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
        indent("// remove untracked files (*.pyc for example)", level=2),
        indent("sh 'git clean -fxd'", level=2),
        indent('}'),
    ]

    if vsc_ci_cfg[RUN_SHELLCHECK]:
        # see https://github.com/koalaman/shellcheck#installing
        shellcheck_url = 'https://storage.googleapis.com/shellcheck/shellcheck-latest.linux.x86_64.tar.xz'
        lines.extend([indent("stage ('shellcheck') {"),
            indent("sh 'curl --silent %s --output - | tar -xJv'" % shellcheck_url, level=2),
            indent("sh 'cp shellcheck-latest/shellcheck .'", level=2),
            indent("sh 'rm -r shellcheck-latest'", level=2),
            indent("sh './shellcheck --version'", level=2),
            indent("sh './shellcheck bin/*.sh'", level=2),
            indent('}')
        ])


    lines.append(indent("stage('test') {"))
    lines.extend([indent("sh '%s'" % c, level=2) for c in test_cmds])
    lines.append(indent('}'))

    if vsc_ci_cfg[JIRA_ISSUE_ID_IN_PR_TITLE]:
        lines.extend([
            indent("stage('PR title JIRA link') {"),
            indent("if (env.CHANGE_ID) {", level=2),
            indent("if (env.CHANGE_TITLE =~ /\s+\(?HPC-\d+\)?/) {", level=3),
            indent('echo "title ${env.CHANGE_TITLE} seems to contain JIRA ticket number."', level=4),
            indent("} else {", level=3),
            indent("echo \"ERROR: title ${env.CHANGE_TITLE} does not end in 'HPC-number'.\"", level=4),
            indent('error("malformed PR title ${env.CHANGE_TITLE}.")', level=4),
            indent('}', level=3),
            indent('}', level=2),
            indent('}'),
        ])

    lines.append('}')

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
