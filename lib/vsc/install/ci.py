#
# Copyright 2019-2023 Ghent University
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
import configparser
import yaml

from pathlib import Path
from vsc.install.shared_setup import (
    MAX_SETUPTOOLS_VERSION_PY36, MAX_SETUPTOOLS_VERSION_PY39,
    vsc_setup,
    )


JENKINSFILE = 'Jenkinsfile'
TOX_INI = 'tox.ini'

VSC_CI = 'vsc-ci'
VSC_CI_INI = VSC_CI + '.ini'

GITHUB_ACTIONS = ".github/workflows/unittest.yml"

ADDITIONAL_TEST_COMMANDS = 'additional_test_commands'
HOME_INSTALL = 'home_install'
INHERIT_SITE_PACKAGES = 'inherit_site_packages'
INSTALL_SCRIPTS_PREFIX_OVERRIDE = 'install_scripts_prefix_override'
JIRA_ISSUE_ID_IN_PR_TITLE = 'jira_issue_id_in_pr_title'
MOVE_SETUP_CFG = 'move_setup_cfg'
PIP_INSTALL_TEST_DEPS = 'pip_install_test_deps'
PIP_INSTALL_TOX = 'pip_install_tox'
PIP3_INSTALL_TOX = 'pip3_install_tox'
EASY_INSTALL_TOX = 'easy_install_tox'
PY3_ONLY = 'py3_only'
PY3_TESTS_MUST_PASS = 'py3_tests_must_pass'
PY36_TESTS_MUST_PASS = 'py36_tests_must_pass'
PY39_TESTS_MUST_PASS = 'py39_tests_must_pass'
RUN_SHELLCHECK = 'run_shellcheck'
ENABLE_GITHUB_ACTIONS = 'enable_github_actions'

logging.basicConfig(format="%(message)s", level=logging.INFO)


def write_file(path, txt):
    """Write specified contents to specified path."""

    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        Path(path).write_text(txt, encoding='utf8')
        logging.info("Wrote %s", path)
    except OSError as err:
        raise OSError(f"Failed to write {path}: {err}") from err

def gen_github_action(repo_base_dir=os.getcwd()):
    """
    Generate tox.ini configuration file for github actions.
    """
    logging.info('[%s]', GITHUB_ACTIONS)
    vsc_ci_cfg = parse_vsc_ci_cfg()

    setup = vsc_setup()
    repofile = os.path.join(repo_base_dir, ".git/config")
    name_url = setup.get_name_url(filename=repofile, version='ALL_VERSIONS')['url']

    if vsc_ci_cfg[ENABLE_GITHUB_ACTIONS]:
        header = [
            f"{GITHUB_ACTIONS}: configuration file for github actions worflow",
            "This file was automatically generated using 'python -m vsc.install.ci'",
            "DO NOT EDIT MANUALLY",
        ]

        txt = ['# ' + l for l in header]
        yaml_content = {
            'name': 'run python tests',
            'on': ['push', 'pull_request'],
            'jobs': {
                'python_unittests': {
                    'runs-on': 'ubuntu-20.04',
                    'strategy': {
                        'matrix': {
                            'python': [3.6, 3.9]
                        }
                    },
                    'steps': [
                        {'name': 'Checkout code', 'uses': 'actions/checkout@v3'},
                        {'name': 'Setup Python', 'uses': 'actions/setup-python@v4',
                         'with': {'python-version': '${{ matrix.python }}'}},
                        # cap versions still compatible with Python 3.6
                        {'name': 'install tox', 'run': "pip install 'virtualenv<20.22.0' 'tox<4.5.0'"},
                        {'name': 'add mandatory git remote',
                         'run': f'git remote add hpcugent {name_url}.git'},
                        {'name': 'Run tox', 'run': 'tox -e py'}
                    ]
                }
            }
        }

        txt.append(yaml.safe_dump(yaml_content))
        return "\n".join(txt)
    else:
        return None

def gen_tox_ini():
    """
    Generate tox.ini configuration file for tox
    see also https://tox.readthedocs.io/en/latest/config.html
    """
    logging.info('[%s]', TOX_INI)

    vsc_ci_cfg = parse_vsc_ci_cfg()

    header = [
        f"{TOX_INI}: configuration file for tox",
        "This file was automatically generated using 'python -m vsc.install.ci'",
        "DO NOT EDIT MANUALLY",
    ]
    header = ['# ' + l for l in header]

    vsc_ci_cfg = parse_vsc_ci_cfg()

    # list of Python environments in which tests should be run
    envs = []

    # always run tests with Python 3.6 and 3.9
    py3_envs = ['py36', 'py39']
    envs.extend(py3_envs)

    pip_args, easy_install_args = '', ''
    if vsc_ci_cfg[INSTALL_SCRIPTS_PREFIX_OVERRIDE]:
        pip_args = '--install-option="--install-scripts={envdir}/bin" '
        easy_install_args = '--script-dir={envdir}/bin '

    lines = header + [
        '',
        "[tox]",
        f"envlist = {','.join(envs)}",
        # instruct tox not to run sdist prior to installing the package in the tox environment
        # (setup.py requires vsc-install, which is not installed yet when 'python setup.py sdist' is run)
        "skipsdist = true",
    ]

    test36 = [
            '',
            '[testenv:py36]',
    ]
    test39 = [
            '',
            '[testenv:py39]',
    ]

    if not vsc_ci_cfg[PY36_TESTS_MUST_PASS]:
        test36.append('ignore_outcome = true')

    if not vsc_ci_cfg[PY39_TESTS_MUST_PASS]:
        test39.append('ignore_outcome = true')

    def make_commands_pre(minor, tlines):
        if minor > 6:
            tlines.append("setenv = SETUPTOOLS_USE_DISTUTILS=local")

        tlines.extend([
            "commands_pre =",
        ])
        if vsc_ci_cfg[MOVE_SETUP_CFG]:
            tlines.append("    mv setup.cfg setup.cfg.moved")

        pip_install_test_deps = vsc_ci_cfg[PIP_INSTALL_TEST_DEPS]
        if pip_install_test_deps:
            for dep in pip_install_test_deps.strip().split('\n'):
                tlines.append(f"    pip install {pip_args}'{dep}'")

        # install required setuptools version;
        # we need a setuptools < 42.0 for now, since in 42.0 easy_install was changed to use pip when available;
        # it's important to use pip (not easy_install) here, since only pip will actually remove an older
        # already installed setuptools version
        if minor > 6:
            tlines.append(f"    pip install {pip_args}'setuptools<{MAX_SETUPTOOLS_VERSION_PY39}' wheel")
        else:
            tlines.append(f"    pip install {pip_args}'setuptools<{MAX_SETUPTOOLS_VERSION_PY36}'")
        # install latest vsc-install release from PyPI;
        # we can't use 'pip install' here, because then we end up with a broken installation because
        # vsc/__init__.py is not installed because we're using pkg_resources.declare_namespace
        # (see https://github.com/pypa/pip/issues/1924)
        if minor > 6:
            tlines.append(f"    python setup.py -q easy_install -v -U {easy_install_args}vsc-install")
        else:
            tlines.append(f"    python -m easy_install -U {easy_install_args}vsc-install")

        if vsc_ci_cfg[MOVE_SETUP_CFG]:
            tlines.append("    mv setup.cfg.moved setup.cfg")

    make_commands_pre(6, test36)
    make_commands_pre(9, test39)

    lines.extend(test36)
    lines.extend(test39)

    lines.extend([
        '',
        '[testenv]',
        "commands = python setup.py test",
        # $USER is not defined in tox environment, so pass it
        # see https://tox.readthedocs.io/en/latest/example/basic.html#passing-down-environment-variables
        'passenv = USER',
    ])

    if vsc_ci_cfg[INHERIT_SITE_PACKAGES]:
        # inherit Python packages installed on the system, if requested
        lines.append("sitepackages = true")

    return '\n'.join(lines) + '\n'


def parse_vsc_ci_cfg():
    """Parse vsc-ci.ini configuration file (if any)."""
    vsc_ci_cfg = {
        ADDITIONAL_TEST_COMMANDS: None,
        HOME_INSTALL: False,
        INHERIT_SITE_PACKAGES: False,
        INSTALL_SCRIPTS_PREFIX_OVERRIDE: False,
        JIRA_ISSUE_ID_IN_PR_TITLE: False,
        MOVE_SETUP_CFG: False,
        PIP_INSTALL_TEST_DEPS: None,
        EASY_INSTALL_TOX: False,
        RUN_SHELLCHECK: False,
        ENABLE_GITHUB_ACTIONS: False,
        PY36_TESTS_MUST_PASS: True,
        PY39_TESTS_MUST_PASS: False,
    }

    deprecated_options = [PY3_ONLY, PY3_TESTS_MUST_PASS, PIP_INSTALL_TOX, PIP3_INSTALL_TOX]

    if os.path.exists(VSC_CI_INI):
        try:
            cfgparser = configparser.ConfigParser()
            cfgparser.read(VSC_CI_INI)
            cfgparser.items(VSC_CI)  # just to make sure vsc-ci section is there
        except (configparser.NoSectionError, configparser.ParsingError) as err:
            logging.error("ERROR: Failed to parse %s: %s", VSC_CI_INI, err)
            sys.exit(1)

        # every entry in the vsc-ci section is expected to be a known setting
        for key, _ in cfgparser.items(VSC_CI):
            if key in vsc_ci_cfg:
                if key in [ADDITIONAL_TEST_COMMANDS, PIP_INSTALL_TEST_DEPS]:
                    vsc_ci_cfg[key] = cfgparser.get(VSC_CI, key)
                else:
                    vsc_ci_cfg[key] = cfgparser.getboolean(VSC_CI, key)
            else:
                if key not in deprecated_options:
                    raise ValueError(f"Unknown key in {VSC_CI_INI}: {key}")

            if key in deprecated_options:
                msg = f'Deprecated: key {key} found in {VSC_CI_INI}. '
                msg += 'It is no longer in use and can safely be removed.'
                logging.warning(msg)

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

    test_cmds = []
    pip_args, easy_install_args = '', ''
    install_subdir = '.vsc-tox'

    # run 'pip3 install' commands in $HOME (rather than in repo checkout) if desired
    if vsc_ci_cfg[HOME_INSTALL]:
        install_cmd = "export PREFIX=$PWD && cd $HOME && pip3 install"
        prefix = os.path.join('$PREFIX', install_subdir)
    else:
        install_cmd = "pip3 install"
        prefix = os.path.join('$PWD', install_subdir)

    python_cmd = 'python3'

    if vsc_ci_cfg[EASY_INSTALL_TOX]:
        # worst case, use 'SETUPTOOLS_USE_DISTUTILS=local python $PREFIX/setup.py -q easy_install -v ' as "easy_install"
        install_cmd = install_cmd.replace('pip3 install', 'python -m easy_install')
        easy_install_args += '-U --user'
        test_cmds.append(f'{install_cmd} {easy_install_args} tox')

    else:
        pip_args += f'--ignore-installed --prefix {prefix}'
        test_cmds.append(f'{install_cmd} {pip_args} tox')

    # Python version to use for updating $PYTHONPATH must be determined dynamically, so use $(...) trick;
    # we must stick to just double strings in the command used to determine the Python version, to avoid
    # that entire shell command is wrapped in triple quotes (which causes trouble)
    pyver_cmd = python_cmd + ' -c "import sys; print(\\\\"%s.%s\\\\" % sys.version_info[:2])"'
    pythonpath = os.path.join('$PWD', install_subdir, 'lib', f'python$({pyver_cmd})', 'site-packages')

    test_cmds.extend([
        # make sure 'tox' command installed is available by updating $PATH and $PYTHONPATH
        ' && '.join([
            f"export PATH={os.path.join('$PWD', install_subdir, 'bin')}:$PATH",
            f'export PYTHONPATH={pythonpath}:$PYTHONPATH',
            f'tox -v -c {TOX_INI}',
        ]),
        # clean up tox installation
        f"rm -r {os.path.join('$PWD', install_subdir)}",
    ])

    additional_test_commands = vsc_ci_cfg[ADDITIONAL_TEST_COMMANDS]
    if additional_test_commands:
        test_cmds.extend(additional_test_commands.strip().split('\n'))

    header = [
        f"{JENKINSFILE}: scripted Jenkins pipefile",
        "This file was automatically generated using 'python -m vsc.install.ci'",
        "DO NOT EDIT MANUALLY",
    ]
    header = ['// ' + line for line in header]

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
            indent(f"sh 'curl -L --silent {shellcheck_url} --output - | tar -xJv'", level=2),
            indent("sh 'cp shellcheck-latest/shellcheck .'", level=2),
            indent("sh 'rm -r shellcheck-latest'", level=2),
            indent("sh './shellcheck --version'", level=2),
            indent("sh './shellcheck bin/*.sh'", level=2),
            indent('}')
        ])

    lines.append(indent("stage('test') {"))
    for test_cmd in test_cmds:
        # be careful with test commands that include single quotes!
        if "'" in test_cmd:
            lines.append(indent(f'sh """{test_cmd}"""', level=2))
        else:
            lines.append(indent(f"sh '{test_cmd}'", level=2))
    lines.append(indent('}'))

    if vsc_ci_cfg[JIRA_ISSUE_ID_IN_PR_TITLE]:
        lines.extend([
            indent("stage('PR title JIRA link') {"),
            indent("if (env.CHANGE_ID) {", level=2),
            indent(r"if (env.CHANGE_TITLE =~ /\s+\(?HPC-\d+\)?/) {", level=3),
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

    github_actions = os.path.join(cwd, GITHUB_ACTIONS)
    github_actions_txt = gen_github_action()
    if github_actions_txt is not None:
        write_file(github_actions, github_actions_txt)

if __name__ == '__main__':
    main()
