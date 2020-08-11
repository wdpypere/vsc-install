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

HOME_INSTALL = 'home_install'
INHERIT_SITE_PACKAGES = 'inherit_site_packages'
INSTALL_SCRIPTS_PREFIX_OVERRIDE = 'install_scripts_prefix_override'
JIRA_ISSUE_ID_IN_PR_TITLE = 'jira_issue_id_in_pr_title'
PIP_INSTALL_TOX = 'pip_install_tox'
PIP3_INSTALL_TOX = 'pip3_install_tox'
PY3_ONLY = 'py3_only'
PY3_TESTS_MUST_PASS = 'py3_tests_must_pass'
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

    vsc_ci_cfg = parse_vsc_ci_cfg()

    header = [
        "%s: configuration file for tox" % TOX_INI,
        "This file was automatically generated using 'python -m vsc.install.ci'",
        "DO NOT EDIT MANUALLY",
    ]
    header = ['# ' + l for l in header]

    vsc_ci_cfg = parse_vsc_ci_cfg()

    # list of Python environments in which tests should be run
    envs = []

    # don't run tests with Python 2 if 'py3_only' is set in vsc-ci.ini
    if not vsc_ci_cfg[PY3_ONLY]:
        envs.append('py27')

    # always run tests with Python 3
    # (failing tests may be ignored if 'py3_tests_must_pass' is set to 0 in vsc-ci.ini)
    py3_env = 'py36'
    envs.append(py3_env)

    pip_args, easy_install_args = '', ''
    if vsc_ci_cfg[INSTALL_SCRIPTS_PREFIX_OVERRIDE]:
        pip_args = '--install-option="--install-scripts={envdir}/bin" '
        easy_install_args = '--script-dir={envdir}/bin '

    lines = header + [
        '',
        "[tox]",
        "envlist = %s" % ','.join(envs),
        # instruct tox not to run sdist prior to installing the package in the tox environment
        # (setup.py requires vsc-install, which is not installed yet when 'python setup.py sdist' is run)
        "skipsdist = true",
    ]

    if not vsc_ci_cfg[PY3_TESTS_MUST_PASS]:
        lines.extend([
            # ignore failures due to missing Python version
            # python2.7 must always be available though, see Jenkinsfile
            "skip_missing_interpreters = true",
        ])

    lines.extend([
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
    ])

    if vsc_ci_cfg[INHERIT_SITE_PACKAGES]:
        # inherit Python packages installed on the system, if requested
        lines.append("sitepackages = true")

    if not vsc_ci_cfg[PY3_TESTS_MUST_PASS]:
        lines.extend([
            '',
            # allow failing tests in Python 3, for now...
            '[testenv:%s]' % py3_env,
            "ignore_outcome = true"
        ])

    return '\n'.join(lines) + '\n'


def parse_vsc_ci_cfg():
    """Parse vsc-ci.ini configuration file (if any)."""
    vsc_ci_cfg = {
        HOME_INSTALL: False,
        INHERIT_SITE_PACKAGES: False,
        INSTALL_SCRIPTS_PREFIX_OVERRIDE: False,
        JIRA_ISSUE_ID_IN_PR_TITLE: False,
        PIP_INSTALL_TOX: False,
        PIP3_INSTALL_TOX: False,
        PY3_ONLY: False,
        PY3_TESTS_MUST_PASS: False,
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
    ]

    pip_args, easy_install_args = '', ''
    if vsc_ci_cfg[INSTALL_SCRIPTS_PREFIX_OVERRIDE]:
        pip_args = '--install-option="--install-scripts={envdir}/bin" '
        easy_install_args = '--script-dir={envdir}/bin '

    # run 'pip install' commands in $HOME (rather than in repo checkout) if desired
    if vsc_ci_cfg[HOME_INSTALL]:
        install_cmd = "cd $HOME && pip install"
    else:
        install_cmd = "pip install"

    prefix = os.path.join('$PWD', '.vsc-tox')

    if vsc_ci_cfg[PIP_INSTALL_TOX]:
        pip_args += '--ignore-installed --prefix %s' % prefix

        # tox requires zipp: require zipp < 3.0 since newer version are Python 3 only
        tox = '"zipp<3.0" tox'

        test_cmds.extend([
            install_cmd + ' --user --upgrade pip',
            # make sure correct 'pip' installation is used
            'export PATH=$HOME/.local/bin:$PATH && %s %s %s' % (install_cmd, pip_args, tox),
        ])

    elif vsc_ci_cfg[PIP3_INSTALL_TOX]:
        install_cmd = install_cmd.replace('pip ', 'pip3 ')
        pip_args += '--ignore-installed --prefix %s' % prefix
        test_cmds.append('%s %s tox' % (install_cmd, pip_args))

    else:
        install_cmd = install_cmd.replace('pip install', 'python -m easy_install')
        easy_install_args += '-U --user'
        test_cmds.append('%s %s tox' % (install_cmd, easy_install_args))

    test_cmds.extend([
        # make sure 'tox' command installed is available by updating $PATH
        'export PATH=%s:$PATH && tox -v -c %s' % (os.path.join(prefix, 'bin'), TOX_INI),
        # clean up tox installation
        'rm -r $PWD/.vsc-tox',
    ])

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
        # see https://github.com/koalaman/shellcheck#installing-a-pre-compiled-binary
        shellcheck_url = 'https://github.com/koalaman/shellcheck/releases/download/latest/'
        shellcheck_url += 'shellcheck-latest.linux.x86_64.tar.xz'
        lines.extend([
            indent("stage ('shellcheck') {"),
            indent("sh 'curl -L --silent %s --output - | tar -xJv'" % shellcheck_url, level=2),
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
