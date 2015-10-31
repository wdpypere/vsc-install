import os

from unittest import TestCase
from vsc.install.shared_setup import KNOWN_LICENSES, get_md5sum, REPO_BASE_DIR

class LicenseTest(TestCase):
    """License related tests"""

    def test_known_liceses(self):
        """Test the KNOWN_LICENSES"""

        total_licenses = len(KNOWN_LICENSES)
        self.assertEqual(total_licenses, 1,
                         msg='shared_setup has %s licenses' % total_licenses);

        md5sums = []
        for short, data in KNOWN_LICENSES.items():
            # the known text must be in known_licenses dir with the short name
            fn = os.path.join(REPO_BASE_DIR, 'known_licenses', short)
            self.assertTrue(os.path.isfile(fn),
                            msg='license %s is in known_licenses directory'% short)
            md5sum = get_md5sum(fn)
            self.assertEqual(data[0], md5sum,
                             msg='md5sum from KNOWN_LICENSES matches the one in known_licenses dir for %s' % short )
            self.assertFalse(md5sum in md5sums,
                             msg='md5sum for license %s is unique' % md5sum)
