import os

from vsc.install.testing import TestCase
from vsc.install.shared_setup import KNOWN_LICENSES, get_md5sum, get_license, REPO_BASE_DIR
from vsc.install.shared_setup import PYPI_LICENSES, release_on_pypi

class LicenseTest(TestCase):
    """License related tests"""

    def test_known_licenses(self):
        """Test the KNOWN_LICENSES"""

        total_licenses = len(KNOWN_LICENSES)
        self.assertEqual(total_licenses, 3,
                         msg='shared_setup has %s licenses' % total_licenses);

        md5sums = []
        for short, data in KNOWN_LICENSES.items():
            # the known text must be in known_licenses dir with the short name
            fn = os.path.join(REPO_BASE_DIR, 'known_licenses', short)
            self.assertTrue(os.path.isfile(fn),
                            msg='license %s is in known_licenses directory'% short)

            md5sum = get_md5sum(fn)
            self.assertEqual(data[0], md5sum,
                             msg='md5sum from KNOWN_LICENSES %s matches the one in known_licenses dir %s for %s' %
                             (data[0], md5sum, short) )
            self.assertFalse(md5sum in md5sums,
                             msg='md5sum for license %s is unique' % md5sum)

            lic_name, classifier = get_license(license=fn)
            self.assertEqual(lic_name, os.path.basename(fn),
                             msg='file %s is license %s' % (fn, lic_name))
            self.assertTrue(classifier.startswith('License :: OSI Approved :: ') or
                            classifier == 'License :: Other/Proprietary License',
                            msg='classifier as expected for %s' % short)

    def test_release_on_pypi(self):
        """Release on pypi or not"""

        self.assertEqual(PYPI_LICENSES, ['LGPLv2+', 'GPLv2'], 'Expected licenses that allow releasing on pypi')

        for short in KNOWN_LICENSES.keys():
            self.assertEqual(release_on_pypi(short), short in PYPI_LICENSES,
                             msg='can %s be usd to release on pypi' % short)
