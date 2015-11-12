import os

from vsc.install.shared_setup import REPO_TEST_DIR, get_name_url

from vsc.install.testing import TestCase

class TestSetup(TestCase):
    """Test shared_setup"""

    def test_get_name_url(self):
        """Test naming function"""
        res = {
            'name': 'vsc-install',
            'url': 'https://github.com/hpcugent/vsc-install',
            'download_url': 'https://github.com/hpcugent/vsc-install/archive/0.1.2.tar.gz',
        }
        for fn in ['PKG-INFO', 'git_config', 'git_config_1', 'git_config_2', 'git_config_3', 'git_config_4']:
            self.assertEqual(get_name_url(os.path.join(REPO_TEST_DIR, 'setup', fn), version='0.1.2'), res,
                             msg='determined name and url from %s file' % fn)

        res.pop('download_url')
        fn = 'git_config'
        self.assertEqual(get_name_url(os.path.join(REPO_TEST_DIR, 'setup', fn), version='0.1.2', license_name='LGPLv2+'), res,
                         msg='determined name and url from %s file with license' % fn)
