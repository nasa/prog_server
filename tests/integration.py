# Copyright © 2021 United States Government as represented by the Administrator of the National Aeronautics and Space Administration. All Rights Reserved.

import unittest
import time
import prog_client, prog_server

TIMEOUT = 10  # Server startup timeout in seconds


class IntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        prog_server.start()
        for i in range(TIMEOUT):
            if prog_server.is_running():
                return
            time.sleep(1)
        prog_server.stop()
        raise Exception("Server startup timeout")

    def test_integration(self):
        from prog_models.models import ThrownObject
        session = prog_client.Session('ThrownObject', state_est_cfg={'x0_uncertainty': 0})
        m = ThrownObject()  # For comparison
        (_, x) = session.get_state()
        x0 = m.initialize()
        for key, value in x.mean.items():
            self.assertAlmostEqual(value, x0[key])
        
        (_, es) = session.get_event_state()
        es0 = m.event_state(x0)
        for key, value in es.mean.items():
            self.assertAlmostEqual(value, es0[key])

        (_, pm) = session.get_performance_metrics()
        self.assertDictEqual(pm.mean, {})

        for i in range(10):
            x0 = m.next_state(x0, {}, 0.1)
            print("x0", x0)
            session.send_data(i/10.0, **m.output(x0))
            time.sleep(0.1)

        time.sleep(1)
        print(session.get_state())

   
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
