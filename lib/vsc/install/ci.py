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
from __future__ import print_function
from optparse import OptionParser
import logging
import os
import sys


JENKINSFILE = 'Jenkinsfile'
TOX_INI = 'tox.ini'

logging.basicConfig(format="%(message)s", level=logging.INFO)
LOG = logging.getLogger()


def parse_options(args):
    """Parse options."""
    parser = OptionParser()

    parser.add_option('-f', '--force', dest='force', action='store_true', help="Use force to overwrite existing files")

    return parser.parse_args(args=args)


def write_file(path, txt, force=False):
    """Write specified contents to specified path."""
    try:
        if os.path.exists(path):
            if force:
                LOG.info("Found existing file %s, overwriting it since --force is used!", path)
            else:
                raise IOError("File %s already exists, use --force to overwrite!" % path)
        with open(path, 'w') as handle:
            handle.write(txt)
        LOG.info("Wrote %s", path)
    except (IOError, OSError) as err:
        raise IOError("Failed to write %s in %s: %s" % (path, os.getcwd(), err))


def gen_tox_ini(force=False):
    """Generate tox.ini"""
    LOG.info('[%s]', TOX_INI)

    cwd = os.getcwd()
    tox_ini = os.path.join(cwd, TOX_INI)

    txt = ''
    write_file(tox_ini, txt, force=force)


def gen_jenkinsfile(force=False):
    """Generate Jenkinsfile."""
    LOG.info('[%s]', JENKINSFILE)

    cwd = os.getcwd()
    jenkinsfile = os.path.join(cwd, JENKINSFILE)

    txt = ''
    write_file(jenkinsfile, txt, force=force)


def main():
    """Main function: generate tox.ini and Jenkinsfile (in current directory)."""

    (options, args) = parse_options(sys.argv)
    if args:
        raise ValueError("Unexpected arguments found: %s" % args)

    gen_tox_ini(force=options.force)

    gen_jenkinsfile(force=options.force)


if __name__ == '__main__':
    main()
