# don't import VSCImportTest, it will trigger the tests
import vsc.install.testing

class ImportTest(vsc.install.testing.VSCImportTest):
    EXCLUDE_MODS = ['^vsc\.fancylogger$'] # it requires vsc-base
