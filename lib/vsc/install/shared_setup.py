#
# Copyright 2011-2015 Ghent University
#
# This file is part of vsc-install,
# originally created by the HPC team of Ghent University (http://ugent.be/hpc/en),
# with support of Ghent University (http://ugent.be/hpc),
# the Flemish Supercomputer Centre (VSC) (https://vscentrum.be/nl/en),
# the Hercules foundation (http://www.herculesstichting.be/in_English)
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
Shared module for vsc software setup

@author: Stijn De Weirdt (Ghent University)
@author: Andy Georges (Ghent University)
"""
import glob
import hashlib
import inspect
import os
import shutil
import sys
import re


import setuptools.command.test

from distutils import log  # also for setuptools
from distutils.dir_util import remove_tree

from setuptools.command.test import test as TestCommand
from setuptools.command.test import ScanningLoader
from setuptools import setup
from setuptools.command.bdist_rpm import bdist_rpm as orig_bdist_rpm
from setuptools.command.build_py import build_py
from setuptools.command.egg_info import egg_info
from setuptools.command.install_scripts import install_scripts
# egg_info uses sdist directly through manifest_maker
from setuptools.command.sdist import sdist

from unittest import TestSuite

have_xmlrunner = None
try:
    import xmlrunner
    have_xmlrunner = True
except ImportError:
    have_xmlrunner = False


# private class variables to communicate
# between VscScanningLoader and VscTestCommand
# stored in __builtin__ because the (Vsc)TestCommand.run_tests
# reloads and cleans up the modules
import __builtin__
if not hasattr(__builtin__,'__target'):
    setattr(__builtin__, '__target', {})

if not hasattr(__builtin__,'__test_filter'):
    setattr(__builtin__, '__test_filter',  {
        'module': None,
        'function': None,
        'allowmods': [],
    })

# Keep this for legacy reasons, setuptools didn't used to be a requirement
has_setuptools = True

# redo log info / warn / error
# don't do it twice
if log.Log.__name__ != 'NewLog':
    # make a map between level and names
    log_levels = dict([(getattr(log,x), x) for x in dir(log) if x == x.upper()])

    OrigLog = log.Log

    class NewLog(OrigLog):
        def _log(self, level, msg, args):
            """Prefix the message with human readbale level"""
            newmsg = "%s: %s" % (log_levels.get(level, 'UNKNOWN'), msg)
            return OrigLog._log(self, level, newmsg, args)

    log.Log = NewLog
    log._global_log = NewLog()
    for lvl in log_levels.values():
        name = lvl.lower()
        setattr(log, name, getattr(log._global_log, name))

    log.set_verbosity(log.DEBUG)


# available authors
ag = ('Andy Georges', 'andy.georges@ugent.be')
eh = ('Ewan Higgs', 'Ewan.Higgs@UGent.be')
jt = ('Jens Timmermans', 'jens.timmermans@ugent.be')
kh = ('Kenneth Hoste', 'kenneth.hoste@ugent.be')
kw = ('Kenneth Waegeman', 'Kenneth.Waegeman@UGent.be')
lm = ('Luis Fernando Munoz Meji?as', 'luis.munoz@ugent.be')
sdw = ('Stijn De Weirdt', 'stijn.deweirdt@ugent.be')
wdp = ('Wouter Depypere', 'wouter.depypere@ugent.be')
wp = ('Ward Poelmans', 'Ward.Poelmans@UGent.be')

# Regexp used to remove suffixes from scripts when installing(/packaging)
REGEXP_REMOVE_SUFFIX = re.compile(r'(\.(?:py|sh|pl))$')

# We do need all setup files to be included in the source dir
# if we ever want to install the package elsewhere.
EXTRA_SDIST_FILES = ['setup.py']

# Put unittests under this directory
DEFAULT_TEST_SUITE = 'test'
DEFAULT_LIB_DIR = 'lib'

URL_GH_HPCUGENT = 'https://github.com/hpcugent/%(name)s'
URL_GHUGENT_HPCUGENT = 'https://github.ugent.be/hpcugent/%(name)s'

RELOAD_VSC_MODS = False

VERSION = '0.9.6'

# list of non-vsc packages that need python- prefix for correct rpm dependencies
# vsc packages should be handled with clusterbuildrpm
PREFIX_PYTHON_BDIST_RPM = ('setuptools',)

# determine the base directory of the repository
# set it via REPO_BASE_DIR (mainly to support non-"python setup" usage/hacks)
_repo_base_dir_env = os.environ.get('REPO_BASE_DIR', None)
if _repo_base_dir_env:
    REPO_BASE_DIR=_repo_base_dir_env
    log.warn('run_tests from base dir set though environment %s' % (REPO_BASE_DIR))
else:
    # we will assume that the tests are called from
    # a 'setup.py' like file in the basedirectory
    # (but could be called anything, as long as it is in the basedir)
    _setup_py = os.path.abspath(sys.argv[0])
    REPO_BASE_DIR = os.path.dirname(_setup_py)
    log.info('run_tests from base dir %s (using executable %s)' % (REPO_BASE_DIR, _setup_py))
REPO_LIB_DIR = os.path.join(REPO_BASE_DIR, DEFAULT_LIB_DIR)
REPO_SCRIPTS_DIR = os.path.join(REPO_BASE_DIR, 'bin')
REPO_TEST_DIR = os.path.join(REPO_BASE_DIR, DEFAULT_TEST_SUITE)

# to be inserted in sdist version of shared_setup
NEW_SHARED_SETUP_HEADER_TEMPLATE = """
# Inserted %s
# Based on shared_setup version %s
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '%s'))

"""

# location of README file
README = 'README.md'

# location of LICENSE file
LICENSE = 'LICENSE'

# key = short name, value tuple
#    md5sum of LICENSE file
#    classifier (see https://pypi.python.org/pypi?%3Aaction=list_classifiers)
# LGPLv2+ and LGPLv2 have same text, we assume always to use the + one
# GPLv2 and GPLv2+ have same text, we assume always to use the regular one
KNOWN_LICENSES = {
    #'LGPLv2' : ('? same text as LGPLv2+', 'License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)'),
    'LGPLv2+' : ('5f30f0716dfdd0d91eb439ebec522ec2', 'License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)'),
    'GPLv2': ('b234ee4d69f5fce4486a80fdaf4a4263', 'License :: OSI Approved :: GNU General Public License v2 (GPLv2)'),
    #'GPLv2+': ('? same text as GPLv2', 'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)'),
    'ARR': ('4c917d76bb092659fa923f457c72d033', 'License :: Other/Proprietary License'),
}

def get_name_url(filename=None, version=None):
    """
    Determine name and url of project
    """

    if filename is None:
        git_config = os.path.join(REPO_BASE_DIR, '.git', 'config')
        pkg_info = os.path.join(REPO_BASE_DIR, 'PKG-INFO')
        if os.path.isfile(pkg_info):
            # e.g. from sdist
            filename = pkg_info
        elif os.path.isfile(git_config):
            filename = git_config

    if filename is None:
        raise Exception('no file to get name from')
    elif not os.path.isfile(filename):
        raise Exception('cannot find file %s to get name from' % filename)

    txt = open(filename).read()

    # First ones are from PKG-INFO
    # second one is .git/config

    # multiline search
    # github pattern for hpcugent, not fork
    all_patterns = {
        'name': [
            r'^Name:\s*(.*?)\s*$',
            r'^\s*url\s*=.*/([^/]*?)(?:\.git)?\s*$',
        ],
        'url': [
            r'^Home-page:\s*(.*?)\s*$',
            r'^\s*url\s*=\s*(https?.*?github.*?[:/]hpcugent/.*?)\.git\s*$',
            r'^\s*url\s*=\s*(git[:@].*?github.*?[:/]hpcugent/.*?)(?:\.git)?\s*$',
        ],
        'download_url' : [
            r'^Download-URL:\s*(.*?)\s*$',
        ],
    }

    res = {}
    for name, patterns in all_patterns.items():
        for pat in patterns:
            reg = re.search(pat, txt, re.M)
            if reg:
                res[name] = reg.group(1)
                log.info('found match %s %s in %s' % (name, res[name], filename))
                break

    # handle git@server:user/project
    reg = re.search(r'^git@(.*?):(.*)$', res.get('url', ''))
    if reg:
        res['url'] = "https://%s/%s" % (reg.group(1), reg.group(2))

    # handle git://server/user/project
    if res['url'].startswith('git://'):
        res['url'] = "https://%s" % res['url'][len('git://'):]

    if not 'download_url' in res and 'github' in res.get('url', '') and version is not None:
        res['download_url'] = "%s/archive/%s-%s.tar.gz" % (res['url'], res['name'], version)

    if len(res) != 3:
        raise Exception("Cannot determine name, url and downlaod url from filename %s: got %s" % (filename, res))
    else:
        log.info('get_name_url returns %s' % res)
        return res


def rel_gitignore(paths):
    """
    A list of paths, return list of relative paths to REPO_BASE_DIR,
    filter with primitive gitignore
    """
    res = [os.path.relpath(p, REPO_BASE_DIR) for p in paths]

    # primitive gitignore
    gitignore = os.path.join(REPO_BASE_DIR, '.gitignore')
    if os.path.isfile(gitignore):
        patterns = [l.strip().replace('*','.*') for l in open(gitignore).readlines() if l.startswith('*')]
        reg = re.compile('^('+'|'.join(patterns)+')$')
        res = [f for f in res if not reg.search(f)]
    return res


def files_in_packages():
    """
    Gather all __init__ files provided by the lib/ subdir
        filenames are relative to the REPO_BASE_DIR
    Return dict  with key
        packages: a dict with key the package and value all files in the package directory
        modules: dict with key non=package module name and value the filename
    """
    res = {'packages' : {}, 'modules': {}}
    offset = len(REPO_LIB_DIR.split(os.path.sep))
    for root, _, files in os.walk(REPO_LIB_DIR):
        package = '.'.join(root.split(os.path.sep)[offset:])
        if '__init__.py' in files:
            if package == 'vsc' or package.startswith('vsc.'):
                init = open(os.path.join(root, '__init__.py')).read()
                if not re.search(r'^import\s+pkg_resources\npkg_resources.declare_namespace\(__name__\)$', init, re.M):
                    raise Exception(('vsc namespace packages do not allow non-shared namespace in dir %s.'
                                     'Fix with pkg_resources.declare_namespace') % root)

            res['packages'][package] = rel_gitignore([os.path.join(root, f) for f in files])

            # this is a package, all .py files are modules
            for mod_fn in res['packages'][package]:
                if not mod_fn.endswith('.py') or mod_fn.endswith('__init__.py'):
                    continue
                modname = os.path.basename(mod_fn)[:-len('.py')]
                res['modules']["%s.%s" % (package, modname)] = mod_fn

    return res

FILES_IN_PACKAGES = files_in_packages()


def find_extra_sdist_files():
    """Looks for files to append to the FileList that is used by the egg_info."""
    log.info("looking for extra dist files")
    filelist = []
    for fn in EXTRA_SDIST_FILES:
        if os.path.isfile(fn):
            filelist.append(fn)
        else:
            log.error("sdist add_defaults Failed to find %s. Exiting." % fn)
            sys.exit(1)
    return filelist


def remove_extra_bdist_rpm_files(pkgs=None):
    """For list of packages pkgs, make the function to exclude all files from rpm"""

    if pkgs is None:
        pkgs = getattr(__builtin__, '__target').get('excluded_pkgs_rpm', [])

    res = []
    for pkg in pkgs:
        res.extend(FILES_IN_PACKAGES['packages'].get(pkg, []))
    log.info('removing files from rpm: %s' % res)

    return res

class vsc_sdist(sdist):
    """
    Upon sdist, add this vsc.install.shared_setup to the sdist
    and modifed the shipped setup.py to be able to use this
    """
    def _mod_setup_py(self, base_dir, external_dir, new_shared_setup):
        """Modify the setup.py in the distribution directory"""

        # re-copy setup.py, to avoid hardlinks
        # (code based on setuptools.command.sdist make_release_tree method)
        dest = os.path.join(base_dir, 'setup.py')
        log.info('recopying dest %s if hardlinked' % dest)
        if hasattr(os, 'link') and os.path.exists(dest):
            # unlink and re-copy, since it might be hard-linked, and
            # we don't want to change the source version
            os.unlink(dest)
            self.copy_file(os.path.join(REPO_BASE_DIR, 'setup.py'), dest)

        fh = open(dest, 'r')
        code = fh.read()
        fh.close()

        # look for first line that does someting with vsc.install and shared_setup
        reg = re.search(r'^.*vsc.install.*shared_setup.*$', code, re.M)
        if not reg:
            raise Exception("No vsc.install shared_setup in setup.py?")

        # insert sys.path hack
        before = reg.start()
        # no indentation
        code = code[:before] + NEW_SHARED_SETUP_HEADER_TEMPLATE % (new_shared_setup, VERSION, external_dir) + code[before:]

        # replace 'vsc.install.shared_setup' -> new_shared_setup
        code = re.sub(r'vsc\.install\.shared_setup', new_shared_setup, code)
        # replace 'from vsc.install import shared_setup' -> import new_shared_setup as shared_setup
        code = re.sub(r'from\s+vsc.install\s+import\s+shared_setup', 'import %s as shared_setup', code)

        # write it
        fh = open(dest, 'w')
        fh.write(code)
        fh.close()

    def _add_shared_setup(self, base_dir, external_dir, new_shared_setup):
        """Create the new shared_setup in distribution directory"""

        ext_dir = os.path.join(base_dir, external_dir)
        os.mkdir(ext_dir)

        dest = os.path.join(ext_dir, '%s.py' % new_shared_setup)
        log.info('inserting shared_setup as %s' % dest)
        try:
            source_code = inspect.getsource(sys.modules[__name__])
        except Exception as err: # have no clue what exceptions inspect might throw
            raise Exception("sdist requires access shared_setup source (%s)" % err)

        try:
            fh = open(dest, 'w')
            fh.write(source_code)
            fh.close()
        except IOError as err:
            raise IOError("Failed to write new_shared_setup source to %s (%s)" % (dest, err))

    def make_release_tree(self, base_dir, files):
        """
        Create the files in subdir base_dir ready for packaging
        After the normal make_release_tree ran, we insert shared_setup
        and modify the to-be-packaged setup.py
        """

        log.info("sdist make_release_tree original base_dir %s files %s" % (base_dir, files))
        log.info("sdist from shared_setup %s current dir %s" % (__file__, os.getcwd()))
        if os.path.exists(base_dir):
            # no autocleanup?
            # can be a leftover of earlier crash/raised exception
            raise Exception("base_dir %s present. Please remove it" % base_dir)

        sdist.make_release_tree(self, base_dir, files)

        if __name__ == '__main__':
            log.info('running shared_setup as main, not adding it to sdist')
        else:
            # use a new name, to avoid confusion with original
            new_shared_setup = 'shared_setup_dist_only'
            external_dir = 'external_dist_only'
            self._mod_setup_py(base_dir, external_dir, new_shared_setup)

            self._add_shared_setup(base_dir, external_dir, new_shared_setup)

        # Add mandatory files
        for fn in [LICENSE, README]:
            self.copy_file(os.path.join(REPO_BASE_DIR, fn), os.path.join(base_dir, fn))


class vsc_egg_info(egg_info):
    """Class to determine the set of files that should be included.

    This amounts to including the default files, as determined by setuptools, extended with the
    few extra files we need to add for installation purposes.
    """

    def finalize_options(self, *args, **kwargs):
        """Handle missing lib dir for scripts-only packages"""
        # the egginfo data will be deleted as part of the cleanup
        cleanup = []
        if not os.path.exists(REPO_LIB_DIR):
            log.warn('vsc_egg_info create missing %s (will be removed later)' % REPO_LIB_DIR)
            os.mkdir(REPO_LIB_DIR)
            cleanup.append(REPO_LIB_DIR)

        res = egg_info.finalize_options(self, *args, **kwargs)

        # cleanup any diretcories created
        for directory in cleanup:
            shutil.rmtree(directory)

        return res

    def find_sources(self):
        """Default lookup."""
        egg_info.find_sources(self)
        self.filelist.extend(find_extra_sdist_files())


class vsc_bdist_rpm_egg_info(vsc_egg_info):
    """Class to determine the source files that should be present in an (S)RPM.

    All __init__.py files that augment package packages should be installed by the
    dependent package, so we need not install it here.
    """

    def find_sources(self):
        """Finds the sources as default and then drop the cruft."""
        vsc_egg_info.find_sources(self)
        for fn in remove_extra_bdist_rpm_files():
            log.debug("removing %s from source list" % (fn))
            if fn in self.filelist.files:
                self.filelist.files.remove(fn)


class vsc_install_scripts(install_scripts):
    """Create the (fake) links for mympirun also remove .sh and .py extensions from the scripts."""

    def __init__(self, *args):
        install_scripts.__init__(self, *args)
        self.original_outfiles = None

    def run(self):
        # old-style class
        install_scripts.run(self)

        self.original_outfiles = self.get_outputs()[:]  # make a copy
        self.outfiles = []  # reset it
        for script in self.original_outfiles:
            # remove suffixes for .py and .sh
            if REGEXP_REMOVE_SUFFIX.search(script):
                newscript = REGEXP_REMOVE_SUFFIX.sub('', script)
                shutil.move(script, newscript)
                script = newscript
            self.outfiles.append(script)


class vsc_build_py(build_py):
    def find_package_modules (self, package, package_dir):
        """Extend build_by (not used for now)"""
        result = build_py.find_package_modules(self, package, package_dir)
        return result


class vsc_bdist_rpm(orig_bdist_rpm):
    """
    Custom class to build the RPM, since the __init__.py cannot be included for the packages
    that have package spread across all of the machine.
    """
    def run(self):
        log.info("vsc_bdist_rpm = %s" % (self.__dict__))
        SHARED_TARGET['cmdclass']['egg_info'] = vsc_bdist_rpm_egg_info  # changed to allow removal of files
        self.run_command('egg_info')  # ensure distro name is up-to-date
        orig_bdist_rpm.run(self)


def filter_testsuites(testsuites):
    """(Recursive) filtering of (suites of) tests"""
    test_filter = getattr(__builtin__, '__test_filter')['function']

    res = type(testsuites)()

    for ts in testsuites:
        # ts is either a test or testsuite of more tests
        if isinstance(ts, TestSuite):
            res.addTest(filter_testsuites(ts))
        else:
            if re.search(test_filter, ts._testMethodName):
                res.addTest(ts)
    return res


class VscScanningLoader(ScanningLoader):
    """The class to look for tests"""

    TEST_LOADER_MODULE = __name__

    def loadTestsFromModule(self, module):
        """
        Support test module and function name based filtering
        """
        try:
            testsuites = ScanningLoader.loadTestsFromModule(self, module)
        except:
            log.error('Failed to load tests from module %s', module)
            raise

        test_filter = getattr(__builtin__,'__test_filter')

        res = testsuites

        if test_filter['module'] is not None:
            name = module.__name__
            if name in test_filter['allowmods']:
                # a parent name space
                pass
            elif re.search(test_filter['module'], name):
                if test_filter['function'] is not None:
                    res = filter_testsuites(testsuites)
                # add parents (and module itself)
                pms = name.split('.')
                for pm_idx in range(len(pms)):
                    pm = '.'.join(pms[:pm_idx])
                    if not pm in test_filter['allowmods']:
                        test_filter['allowmods'].append(pm)
            else:
                res = type(testsuites)()

        return res


class VscTestCommand(TestCommand):
    """
    The cmdclass for testing
    """

    # make 2 new 'python setup.py test' options available
    user_options = TestCommand.user_options + [
        ('test-filterf=', 'f', "Regex filter on test function names"),
        ('test-filterm=', 'F', "Regex filter on test (sub)modules"),
        ('test-xmlrunner=', 'X', "use XMLTestRunner with value as output name (e.g. test-reports)"),
    ]

    TEST_LOADER_CLASS = VscScanningLoader

    def initialize_options(self):
        """
        Add attributes for new commandline options and set test_loader
        """
        TestCommand.initialize_options(self)
        self.test_filterm = None
        self.test_filterf = None
        self.test_xmlrunner = None

        self.test_loader = '%s:%s' % (self.TEST_LOADER_CLASS.TEST_LOADER_MODULE, self.TEST_LOADER_CLASS.__name__)
        log.info("test_loader set to %s" % self.test_loader)

    def setup_sys_path(self):
        """
        Prepare sys.path to be able to
            use the modules provided by this package (assumeing they are in 'lib')
            use any scripts as modules (for unittesting)
            use the test modules as modules (for unittesting)
        Returns a list of directories to cleanup
        """
        cleanup = []

        # make a lib dir to trick setup.py to package this properly
        # and git ignore empty dirs, so recreate it if necessary
        if not os.path.exists(REPO_LIB_DIR):
            os.mkdir(REPO_LIB_DIR)
            cleanup.append(REPO_LIB_DIR)

        if os.path.isdir(REPO_TEST_DIR):
            sys.path.insert(0, REPO_TEST_DIR)
        else:
            raise Exception("Can't find location of testsuite directory %s in %s" % (DEFAULT_TEST_SUITE, REPO_BASE_DIR))

        # insert REPO_BASE_DIR, so import DEFAULT_TEST_SUITE works (and nothing else gets picked up)
        sys.path.insert(0, REPO_BASE_DIR)

        # make sure we can import the script as a module
        if os.path.isdir(REPO_SCRIPTS_DIR):
            sys.path.insert(0, REPO_SCRIPTS_DIR)

        return cleanup

    def reload_modules(self, package):
        """
        Cleanup and restore package because we use
        vsc package tools very early.
        So we need to make sure they are picked up from the paths as specified
        in setup_sys_path, not to mix with installed and already loaded modules
        """

        def candidate(modulename):
            """Select candidate modules to reload"""
            return modulename in (package,) or modulename.startswith(package+'.')

        loaded_modules = filter(candidate, sys.modules.keys())
        reload_modules = []
        for name in loaded_modules:
            if hasattr(sys.modules[name], '__file__'):
                # only actual modules
                reload_modules.append(name)
            del(sys.modules[name])

        # reimport
        for name in reload_modules:
            __import__(name)

    def force_xmlrunner(self):
        """
        A monkey-patch attempt to run the tests with
        xmlrunner.XMLTestRunner(output=xyz).run(suite)

        E.g. in case of jenkins and you want junit compatible reports
        """
        xmlrunner_output = self.test_xmlrunner

        class OutputXMLTestRunner(xmlrunner.XMLTestRunner):
            """Force the output"""
            def __init__(self, *args, **kwargs):
                kwargs['output'] = xmlrunner_output
                xmlrunner.XMLTestRunner.__init__(self, *args, **kwargs)

        cand_main_names = ['unittest.main', 'unittest_main', 'main']
        for main_name in cand_main_names:
            main_orig = getattr(setuptools.command.test, main_name, None)
            if main_orig is not None:
                break
        if main_orig is None:
            raise Exception("monkey patching XmlRunner failed")

        class XmlMain(main_orig):
            """This is unittest.main with forced usage of XMLTestRunner"""
            def __init__(self, *args, **kwargs):
                kwargs['testRunner'] = OutputXMLTestRunner
                main_orig.__init__(self, *args, **kwargs)

        setattr(setuptools.command.test, main_name, XmlMain)

    def run_tests(self):
        """
        Actually run the tests, but start with
            passing the filter options via __builtin__
            set sys.path
            reload vsc modules
        """
        getattr(__builtin__,'__test_filter').update({
            'function': self.test_filterf,
            'module': self.test_filterm,
        })

        if self.test_xmlrunner is not None:
            if not have_xmlrunner:
                raise Exception('test-xmlrunner requires xmlrunner module')
            self.force_xmlrunner()

        cleanup = self.setup_sys_path()

        if RELOAD_VSC_MODS:
            self.reload_modules('vsc')

        # e.g. common names like test can have existing packages
        if not DEFAULT_TEST_SUITE in sys.modules:
            __import__(DEFAULT_TEST_SUITE)
        self.reload_modules(DEFAULT_TEST_SUITE)

        res = TestCommand.run_tests(self)

        # cleanup any diretcories created
        for directory in cleanup:
            shutil.rmtree(directory)

        return res


def add_and_remove(alist, extra=None, exclude=None):
    """
    alist is a list of strings, it possibly is modified

    extras is a list of strings added to alist
    exclude is list of regex patterns to filter the list of strings
    """
    if extra:
        alist.extend(etxra)
    if exclude:
        for pat in exclude:
            reg = re.compile(pat)
            alist = [s for s in alist if not reg.search(s)]
    log.info('generated list: %s' % alist)
    return alist


def generate_packages(extra=None, exclude=None):
    """
    Walk through lib subdirectory (if any)
        gather all __init__ and build up provided package

    Supports extra and/or exclude from add_and_remove
        extra is a list of packages added to the discovered ones
        exclude is list of regex patterns to filter the packages
    """
    res = add_and_remove(FILES_IN_PACKAGES['packages'].keys(), extra=extra, exclude=exclude)
    log.info('generated packages list: %s' % res)
    return res


def generate_modules(extra=None, exclude=None):
    """
    Return list of non-package modules
    Supports extra and/or exclude from add_and_remove
    """
    res = add_and_remove(FILES_IN_PACKAGES['modules'].keys(), extra=extra, exclude=exclude)
    log.info('generated modules list: %s' % res)
    return res


def generate_scripts(extra=None, exclude=None):
    """Return a list of scripts in REPOS_SCRIPTS_DIR
    Supports extra and/or exclude from add_and_remove
    """
    res = []
    if os.path.isdir(REPO_SCRIPTS_DIR):
        res = rel_gitignore(glob.glob("%s/*" % REPO_SCRIPTS_DIR))
    res = add_and_remove(res, extra=extra, exclude=exclude)
    log.info('generated scripts list: %s' % res)
    return res


# shared target config
SHARED_TARGET = {
    'cmdclass': {
        "bdist_rpm": vsc_bdist_rpm,
        "egg_info": vsc_egg_info,
        "install_scripts": vsc_install_scripts,
        "sdist": vsc_sdist,
        "test": VscTestCommand,
    },
    'download_url': '',
    'package_dir': {'': DEFAULT_LIB_DIR},
    'packages': generate_packages(),
    'setup_requires' : ['setuptools', 'vsc-install >= %s' % VERSION],
    'test_suite': DEFAULT_TEST_SUITE,
    'url': '',
}


def cleanup(prefix=''):
    """Remove all build cruft."""
    dirs = [prefix + 'build'] + glob.glob('%s%s/*.egg-info' % (prefix, DEFAULT_LIB_DIR))
    for d in dirs:
        if os.path.isdir(d):
            log.warn("cleanup %s" % d)
            try:
                remove_tree(d, verbose=False)
            except OSError, _:
                log.error("cleanup failed for %s" % d)

    for fn in ('setup.cfg',):
        ffn = prefix + fn
        if os.path.isfile(ffn):
            os.remove(ffn)


def sanitize(name):
    """
    Transforms name into a sensible string for use in setup.cfg.

    python- is prefixed in case of
        enviroment variable VSC_INSTALL_PYTHON is set to 1 and either
            name is in hardcoded list PREFIX_PYTHON_BDIST_RPM
            name starts with 'vsc'
    """
    if isinstance(name, basestring):
        p_p = (os.environ.get('VSC_RPM_PYTHON', False) and
               ((name in PREFIX_PYTHON_BDIST_RPM)
                or name.startswith('vsc')))
        if p_p:
            name = 'python-%s' % name

        return name

    return ",".join([sanitize(r) for r in name])


def get_md5sum(filename):
    """Use this function to compute the md5sum in the KNOWN_LICENSES hash"""
    return hashlib.md5(open(filename).read()).hexdigest()

def get_license(license=None):
    """
    Determine the license of this project based on LICENSE file

    license argument is the license file to check. if none rpovided, the project LICENSE is used
    """
    # LICENSE is required and enforced
    if license is None:
        license = os.path.join(REPO_BASE_DIR, LICENSE)
    if not os.path.exists(license):
        raise Exception('LICENSE is missing (was looking for %s)' % license)

    license_md5 = get_md5sum(license)
    log.info('found license %s with md5sum %s' % (license, license_md5))
    found_lic = False
    for lic_short, data in KNOWN_LICENSES.items():
        if license_md5 != data[0]:
            continue

        found_lic = True
        break

    if not found_lic:
        raise Exception('UNKONWN LICENSE %s provided. Should be fixed or added to vsc-install' % license)

    log.info("Found license name %s and classifier %s" , lic_short, data[1])
    return lic_short, data[1]


def parse_target(target, urltemplate=None):
    """
    Add some fields
        get name / url / download_url from project
            deprecated: set url / download_url from urltemplate

        vsc_description: set the description and long_description from the README
        vsc_scripts: generate scripts from bin content

    Remove sdist vsc class with '"vsc_sdist": False' in target
    """
    new_target = {}
    new_target.update(SHARED_TARGET)

    if not 'name' in target:
        log.info('No name defined, trying to determine it')
        # sets name / url and download_url
        target.update(get_name_url(version=target['version']))

    # prepare classifiers
    classifiers = new_target.setdefault('classifiers', [])

    if urltemplate:
        new_target['url'] = urltemplate % target
        if 'github' in urltemplate:
            new_target['download_url'] = "%s/tarball/master" % new_target['url']

    # Readme are required
    readme = os.path.join(REPO_BASE_DIR, README)
    if not os.path.exists(readme):
        raise Exception('README is missing (was looking for %s)' % readme)

    # license info
    lic_name, lic_classifier = get_license()
    log.info('setting license %s' % lic_name)
    new_target['license'] = lic_name
    classifiers.append(lic_classifier)

    vsc_description = target.pop('vsc_description', True)
    if vsc_description:
        if 'long_description' in target:
            log.info(('Going to ignore the provided long_descripton.'
                       'Set it in the %s or disable vsc_description') % README)
        readmetxt = open(readme).read()

        # look for description block, read text until double empty line or new block
        # allow 'words with === on next line' or comment-like block '# title'
        reg = re.compile(r"(?:^(?:^\s*(\S.*?)\s*\n=+)|(?:#+\s+(\S.*?))\s*\n)", re.M)
        headers_blocks = reg.split(readmetxt)
        # there are 2 matching groups, only one can match and it's hard to make a single readable regex
        # so one of the 2 groups gives a None
        headers_blocks = [x for x in headers_blocks if x is not None]
        # using a regex here, to allow easy modifications
        try:
            descr_index = [i for i, txt in enumerate(headers_blocks) if re.search(r'^Description$', txt or '')][0]
            descr = re.split(r'\n\n', headers_blocks[descr_index+1])[0].strip()
            descr = re.sub(r'[\n\t]', ' ', descr) # replace newlines and tabs in description
            descr = re.sub(r'\s+', ' ', descr) # squash whitespace
        except IndexError:
            raise Exception('Could not find a Description block in the README %s to create the long description' % readme)
        log.info('using long_description %s' % descr)
        new_target['description'] = descr # summary in PKG-INFO
        new_target['long_description'] = readmetxt # description in PKG-INFO

    vsc_scripts = target.pop('vsc_scripts', True)
    if vsc_scripts:
        candidates = generate_scripts()
        if candidates:
            if 'scripts' in target:
                old_scripts = target.pop('scripts', [])
                log.info(('Going to ignore specified scripts %s'
                           ' Use "\'vsc_scripts\': False" if you know what you are doing') % old_scripts)
            new_target['scripts'] = candidates

    use_vsc_sdist = target.pop('vsc_sdist', True)
    if not use_vsc_sdist:
        sdist_cmdclass = new_target['cmdclass'].pop('sdist')
        if not issubclass(sdist_cmdclass, vsc_sdist):
            raise Exception("vsc_sdist is disabled, but the sdist command is not a vsc_sdist (sub)class. Clean up your target.")

    for k, v in target.items():
        if k in ('author', 'maintainer'):
            if not isinstance(v, list):
                log.error("%s of config %s needs to be a list (not tuple or string)" % (k, target['name']))
                sys.exit(1)
            new_target[k] = ";".join([x[0] for x in v])
            new_target["%s_email" % k] = ";".join([x[1] for x in v])
        else:
            if isinstance(v, dict):
                # eg command_class
                if not k in new_target:
                    new_target[k] = type(v)()
                new_target[k].update(v)
            else:
                new_target[k] = type(v)()
                new_target[k] += v

    log.debug("New target = %s" % (new_target))
    return new_target


def build_setup_cfg_for_bdist_rpm(target):
    """Generates a setup.cfg on a per-target basis.

    Create [bdist_rpm] section with
        install_requires => requires
        provides => provides
        setup_requires => build_requires

    @type target: dict

    @param target: specifies the options to be passed to setup()
    """

    if target.pop('makesetupcfg', True):
        log.info('makesetupcfg set to True, (re)creating setup.cfg')
    else:
        log.info('makesetupcfg set to False, not (re)creating setup.cfg')
        return

    try:
        setup_cfg = open('setup.cfg', 'w')  # and truncate
    except (IOError, OSError), err:
        print "Cannot create setup.cfg for target %s: %s" % (target['name'], err)
        sys.exit(1)

    txt = ["[bdist_rpm]"]
    if 'install_requires' in target:
        txt.extend(["requires = %s" % (sanitize(target['install_requires']))])

    if 'provides' in target:
        txt.extend(["provides = %s" % (sanitize(target['provides']))])
        target.pop('provides')

    if 'setup_requires' in target:
        txt.extend(["build_requires = %s" % (sanitize(target['setup_requires']))])

    # add metadata
    txt += ['', '[metadata]', '', 'description-file = %s' % README, '']

    setup_cfg.write("\n".join(txt+['']))
    setup_cfg.close()


def prepare_rpm(target):
    """
    Make some preparations required for proepr rpm creation
        exclude files provided by packages that are shared
            excluded_pkgs_rpm: is a list of packages, default to ['vsc']
            set it to None when defining own function
        generate the setup.cfg using build_setup_cfg_for_bdist_rpm
    """
    pkgs = target.pop('excluded_pkgs_rpm', ['vsc'])
    if pkgs is not None:
        getattr(__builtin__, '__target')['excluded_pkgs_rpm'] = pkgs

    build_setup_cfg_for_bdist_rpm(target)


def action_target(target, setupfn=setup, extra_sdist=[], urltemplate=None):
    """
    Additional target attributes
        makesetupcfg: boolean, default True, to generate the setup.cfg (set to False if a manual setup.cfg is provided)
        provides: list of rpm provides for setup.cfg
    """
    do_cleanup = True
    try:
        # very primitive check for install --skip-build
        # in that case, we don't mind "leftover build";
        # it's probably intentional
        install_ind = sys.argv.index('install')
        build_skip = sys.argv.index('--skip-build')
        if build_skip > install_ind:
            do_cleanup = False
    except ValueError:
        pass

    if do_cleanup:
        cleanup()

    prepare_rpm(target)
    x = parse_target(target, urltemplate)

    setupfn(**x)


if __name__ == '__main__':
    """
    This main is the setup.py for vsc-install
    """
    PACKAGE = {
        'version': VERSION,
        'author': [sdw, ag, jt],
        'maintainer': [sdw, ag, jt],
        'install_requires': ['setuptools'],
        'setup_requires': ['setuptools'],
        'excluded_pkgs_rpm': [], # vsc-install ships vsc package (the vsc package is removed by default)
    }

    action_target(PACKAGE)
