# don't import VSCImportTest, it will trigger the tests
import vsc.install.commontest

class ImportTest(vsc.install.commontest.CommonTest):
    EXCLUDE_MODS = ['^vsc\.fancylogger$'] # it requires vsc-base
