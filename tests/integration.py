# Copyright © 2021 United States Government as represented by the Administrator of the National Aeronautics and Space Administration. All Rights Reserved.

import unittest
import time
import prog_client, prog_server


class IntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        prog_server.start()
        time.sleep(6)

    def test_integration(self):
        from prog_models.models import ThrownObject
        session = prog_client.Session('ThrownObject', state_est_cfg={'x0_uncertainty': 0})
        m = ThrownObject()  # For comparison
        x = session.get_state()
        x0 = m.initialize()
        for key, value in x.mean.items():
            self.assertAlmostEqual(value, x0[key])
        
        es = session.get_event_state()
        es0 = m.event_state(x0)
        for key, value in es.mean.items():
            self.assertAlmostEqual(value, es0[key])

        pm = session.get_performance_metrics()
        self.assertDictEqual(pm.mean, {})
   
    @classmethod
    def tearDownClass(cls):
        prog_server.stop()

# This allows the module to be executed directly    
def run_tests():
    l = unittest.TestLoader()
    runner = unittest.TextTestRunner()
    print("\n\nTesting prog_client with prog_server")
    result = runner.run(l.loadTestsFromTestCase(IntegrationTest)).wasSuccessful()

    if not result:
        raise Exception("Failed test")

if __name__ == '__main__':
    run_tests()
