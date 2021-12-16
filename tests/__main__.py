# Copyright © 2021 United States Government as represented by the Administrator of the National Aeronautics and Space Administration. All Rights Reserved.

import unittest
import pkgutil
from importlib import import_module

if __name__ == '__main__':
    l = unittest.TestLoader()

    was_successful = True

    for _, name, _ in pkgutil.iter_modules(['tests']):
        if name[0] == '_':
            continue
        print('importing tests.' + name)
        test_module = import_module('tests.' + name)
        try:
            test_module.run_tests()
        except Exception:
            print('Failed test: ' + name)
            was_successful = False

    if not was_successful:
        raise Exception("Failed test")
