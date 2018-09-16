import unittest
import doctest

import os

from glob import glob


def load_tests(loader, tests, ignore):

    _this_dir = os.path.dirname(__file__)

    doctest_flags = doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE

    for f_name in glob(os.path.join(_this_dir, '../traceable_dict/_*.py')):
        tests.addTests(doctest.DocFileSuite(f_name, module_relative=False, optionflags=doctest_flags))

    doc_f_names = list(glob(os.path.join(_this_dir, '../docs/*.rst')))
    tests.addTests(
        doctest.DocFileSuite(*doc_f_names, module_relative=False, optionflags=doctest_flags))

    return tests


if __name__ == '__main__':
    unittest.main()
