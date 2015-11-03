Description
===========
vsc-install provides shared setuptools functions and classes for python libraries developed by UGent's HPC group

Add tests
=========

Test are python modules in the `test` directory which have subclass of `TestCase`
and at least one method that has a name starting with `test_`

You are advised to use
```python
from vsc.install.testing import TestCase
```
(instead of basic `TestCase` from `unittest`).

Initialise the test directory with

```bash
mkdir test
echo '' > test/__init__.py
echo 'from vsc.install.testing import VSCImportTest' > test/00-import.py
```

When the tests are run, `test`, `lib` and `bin` (if relevant) are added to `sys.path`,
so no need to do so in the tets modules.

Run tests
=========

```bash
python setup.py test
```

Filter tests with `-F` (test module names) and `-f` (test method names)

See also
```bash
python setup.py test --help
```

In case following error occurs, it means there is a test module `XYZ` that cannot be imported.

```
  ...
  File "setup.py", line 499, in loadTestsFromModule
     testsuites = ScanningLoader.loadTestsFromModule(self, module)
  File "build/bdist.linux-x86_64/egg/setuptools/command/test.py", line 37, in loadTestsFromModule
  File "/usr/lib64/python2.7/unittest/loader.py", line 100, in loadTestsFromName
    parent, obj = obj, getattr(obj, part)
  AttributeError: 'module' object has no attribute 'XYZ'
```

You can try get the actual import error for fixing the issue with
```bash
python -c 'import sys;sys.path.insert(0, "test");import XYZ;'
```
