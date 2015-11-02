import os

from vsc.install.shared_setup import REPO_TEST_DIR, get_name_url

from vsc.install.testing import TestCase

class TestSetup(TestCase):
    """Test shared_setup"""

    def test_get_name_url(self):
        """Test naming function"""
        res= {
            'name': 'vsc-install',
            'url': 'https://github.com/hpcugent/vsc-install',
            'download_url': 'https://github.com/hpcugent/vsc-install/tarball/master',
        }
        for fn in ['PKG-INFO', 'git_config', 'git_config_1', 'git_config_2']:
            self.assertEqual(get_name_url(os.path.join(REPO_TEST_DIR, 'setup', fn)), res,
                             msg='determined name from %s file' % fn)
