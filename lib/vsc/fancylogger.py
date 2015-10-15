"""
vsc.fancylogger has been deprecated since forever,
vsc.utils.fancylogger should be used instead.

This module provides a migration path away from vsc.fancylogger:
  vsc.fancylogger currently provided by vsc-base, wherever it is used, vsc-base is present
  we start with tracking actual leftover usage
  any code that uses it, should receives updates to use vsc.utils.fancylogger
  in the 1.0.1 release, this file should not be shipped anymore
    (and only requires an update of vsc-install)

At least 'import vsc' can be used now without triggering an import of fancylogger
"""

# it's ok if this fails with only vsc-install installed.
# we cannot introduce a dependency on vsc-base (and we do not care)
from vsc.utils.fancylogger import *

# Deprecation tracker to syslog
logToDevLog(True)
getLogger().error("LEGACYVSCFANCYLOGGER from %s %s", __name__, globals().get('__file__','<nofile>'))
logToDevLog(False)
