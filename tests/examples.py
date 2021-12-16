# Copyright © 2021 United States Government as represented by the Administrator of the National Aeronautics and Space Administration. All Rights Reserved.

import unittest
import time
import prog_server
import sys
from io import StringIO 
import pkgutil
from importlib import import_module

TIMEOUT = 10  # Server startup timeout in seconds

def make_test_function(example):
    def test(self):
        ex = import_module("examples." + example)
        ex.run_example()
    return test


class TestExamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        prog_server.start()
        for i in range(TIMEOUT):
            if prog_server.is_running():
                return
            time.sleep(1)
        prog_server.stop()
        raise Exception("Server startup timeout")

    def setUp(self):
        # set stdout (so it wont print)
        self._stdout = sys.stdout
        sys.stdout = StringIO()

    # def test_online_prog(self):
    #     from examples import online_prog

    #     online_prog.run_example()

    def tearDown(self):
        # reset stdout
        sys.stdout = self._stdout
        
    @classmethod
    def tearDownClass(cls):
        prog_server.stop()


# This allows the module to be executed directly    
def run_tests():
    # Create tests for each example
    for _, name, _ in pkgutil.iter_modules(['examples']):
        test_func = make_test_function(name)
        setattr(TestExamples, 'test_{0}'.format(name), test_func)   

    # Run tests
    l = unittest.TestLoader()
    runner = unittest.TextTestRunner()
    print("\n\nTesting examples (this may take some time)")
    result = runner.run(l.loadTestsFromTestCase(TestExamples)).wasSuccessful()

    if not result:
        raise Exception("Failed test")

if __name__ == '__main__':
    run_tests()
