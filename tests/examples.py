# Copyright © 2021 United States Government as represented by the Administrator of the National Aeronautics and Space Administration. All Rights Reserved.

import unittest
import time
import prog_client, prog_server

TIMEOUT = 10  # Server startup timeout in seconds


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
    
    @classmethod
    def tearDownClass(cls):
        prog_server.stop()


# This allows the module to be executed directly    
def run_tests():
    l = unittest.TestLoader()
    runner = unittest.TextTestRunner()
    print("\n\nTesting prog_client with prog_server")
    result = runner.run(l.loadTestsFromTestCase(TestExamples)).wasSuccessful()

    if not result:
        raise Exception("Failed test")

if __name__ == '__main__':
    run_tests()
