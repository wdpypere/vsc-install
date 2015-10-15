from unittest import TestCase, TestLoader
import vsc.install.shared_setup

class ImportTest(TestCase):
    """Dummy class to prove the shared_setup import works"""

    def test_importok(self):
        """It's ok if we get here"""
        self.assertTrue(True, msg='import vsc.install.shared_setup was success')
