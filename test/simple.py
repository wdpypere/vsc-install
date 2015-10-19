from unittest import TestCase, TestLoader
import sys

import vsc
import vsc.install
import vsc.install.shared_setup

class ImportTest(TestCase):
    """Dummy class to prove importing works"""

    def test_importok(self):
        """It's ok if we get here"""
        self.assertTrue('vsc' in sys.modules, msg='import vsc was success')
        self.assertTrue('vsc.install' in sys.modules, msg='import vsc.install was success')
        self.assertTrue('vsc.install.shared_setup' in sys.modules, msg='import vsc.install.shared_setup was success')
