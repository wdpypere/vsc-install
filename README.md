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

And any `__main__` or `suite()` is not needed (anymore).

Initialise the test directory with

```bash
mkdir -p test
echo '' > test/__init__.py
echo 'from vsc.install.commontest import CommonTest' > test/00-import.py
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

```txt
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

Fix failing tests
=================

* Missing / incorrect `LICENSE`

 * Copy the appropirate license file under `known_licenses` in the project directory and name the file `LICENSE`

* Missing `README.md`

 * Create a `README.md` file with at least a `Description` section

* Fix license headers as described in https://github.com/hpcugent/vsc-install/blob/master/lib/vsc/install/headers.py

  ```
  cd <project dir with .git folder>
  REPO_BASE_DIR=$PWD python -m vsc.install.headers path/to/file script_or_not
  ```

  Fix them all at once using find

  ```
  find ./{lib,test} -type f -name '*.py' | REPO_BASE_DIR=$PWD xargs -I '{}' python -m vsc.install.headers '{}'
  find ./bin -type f -name '*.py' | REPO_BASE_DIR=$PWD xargs -I '{}' python -m vsc.install.headers '{}' 1
  ```

  Do not forget to check the diff
* Python scripts (i.e. with a python shebang and installed as scripts in setup) have to use `#!/usr/bin/env python` as shebang
* Remove any `build_rpms_settings.sh` leftovers
* The `TARGET` dict in `setup.py` should be minimal unless you really know what you are doing (i.e. if it is truly different from defaults)

 * Remove `name`, `scripts`, ...

* `Exception: vsc namespace packages do not allow non-shared namespace`

 * Add to the `__init__.py`

 ```python
 """
 Allow other packages to extend this namespace, zip safe setuptools style
 """
 import pkg_resources
 pkg_resources.declare_namespace(__name__)
 ```
