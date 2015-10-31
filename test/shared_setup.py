import os

from vsc.install.shared_setup import REPO_TEST_DIR, get_name

from unittest import TestCase

class TestSetup(TestCase):
    """Test shared_setup"""
    
    def test_get_name(self):
        """Test naming function"""
        self.assertEqual(get_name(os.path.join(REPO_TEST_DIR, 'setup', 'git_config')), 'vsc-install',
                         msg='determined name from .git/config file')
        self.assertEqual(get_name(os.path.join(REPO_TEST_DIR, 'setup', 'PKG-INFO')), 'vsc-install',
                         msg='determined name from PKG-INFO file')
