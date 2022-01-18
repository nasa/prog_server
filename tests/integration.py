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
        noise = {'x': 0.1, 'v': 0.1}
        if 'max_x' in ThrownObject.states:
            # max_x was removed in the dev branch
            noise['max_x'] = 0
        session = prog_client.Session('ThrownObject', state_est_cfg={'x0_uncertainty': 0}, model_cfg={'process_noise': noise}, pred_cfg={'save_freq': 0.1})
        m = ThrownObject()  # For comparison

        # State
        (_, x) = session.get_state()
        x0 = m.initialize()
        for key, value in x.mean.items():
            self.assertAlmostEqual(value, x0[key])
        
        # Event State
        (_, es) = session.get_event_state()
        es0 = m.event_state(x0)
        for key, value in es.mean.items():
            self.assertAlmostEqual(value, es0[key])

        # Performance Metrics
        (_, pm) = session.get_performance_metrics()
        self.assertDictEqual(pm.mean, {})

        # Prediction Status
        status = session.get_prediction_status()
        self.assertIn('exceptions', status)
        self.assertIn('in progress', status)
        self.assertIn('last prediction', status)
        self.assertListEqual(status['exceptions'], [])
        self.assertIsInstance(status['in progress'], int)
        
        for i in range(5):
            # Wait for prediction to complete
            time.sleep(0.5)
            status = session.get_prediction_status()
            if status['last prediction'] is not None:
                break
        self.assertIsNotNone(status['last prediction'], "Timeout waiting for prediction")

        # Prediction - ToE
        (t_p, ToE) = session.get_predicted_toe()
        self.assertAlmostEqual(t_p, -1e-99)
        self.assertAlmostEqual(ToE.mean['falling'], 4.125, delta=0.1)
        self.assertAlmostEqual(ToE.mean['impact'], 8.3, delta=0.1)

        # Prep Prediction
        (times, _, sim_states, _, sim_es) = m.simulate_to_threshold(lambda t,x=None: {}, threshold_keys='impact', save_freq=0.1, dt=0.1)

        # Prediction - future states
        (t_p, states) = session.get_predicted_state()
        self.assertAlmostEqual(t_p, -1e-99)

        for i in range(len(states.times)):
            self.assertAlmostEqual(states.times[i], i/10)
            for key, value in states.snapshot(i).mean.items():
                if i < len(sim_states):  # may have one or two more states
                    self.assertAlmostEqual(value, sim_states[i][key], delta = (i+1)/15, msg=f"snapshot at {i/10}s for key {key} should be {sim_states[i][key]} was {value}")

        # Prediction - future event_states
        (t_p, states) = session.get_predicted_event_state()
        self.assertAlmostEqual(t_p, -1e-99)

        for i in range(len(states.times)):
            self.assertAlmostEqual(states.times[i], i/10)
            for key, value in states.snapshot(i).mean.items():
                if i < len(sim_es):  # may have one or two more states
                    self.assertAlmostEqual(value, sim_es[i][key], delta = (i+1)/20, msg=f"snapshot at {i/10}s for key {key} should be {sim_es[i][key]} was {value}")

        # Prediction - future performance metrics
        (t_p, states) = session.get_predicted_performance_metrics()
        self.assertAlmostEqual(t_p, -1e-99)
        for i in range(len(states.times)):
            self.assertDictEqual(states.snapshot(i).mean, {})

        # State after sending data
        for i in range(1,11):
            x0 = m.next_state(x0, {}, 0.1)
            session.send_data(i/10.0, **m.output(x0))
            time.sleep(0.1)

        t, x_est = session.get_state()
        self.assertAlmostEqual(t, 1)

        self.assertAlmostEqual(x_est.mean['x'], x0['x'], delta=1)
        self.assertAlmostEqual(x_est.mean['v'], x0['v'], delta=0.75)
        if 'max_x' in ThrownObject.states:
            # max_x was removed in recent version
            self.assertAlmostEqual(x_est.mean['x'], x_est.mean['max_x'], delta=0.2)

        # TODO UPDATED PREDICTION TIME

    def test_error_in_init(self):
        # Invalid model name
        with self.assertRaises(Exception):
            session = prog_client.Session("fake model")

        # Model init - process noise has non-existent state
        # with self.assertRaises(Exception):
        #     session = prog_client.Session('ThrownObject', model_cfg={'process_noise': {'x': 0.1, 'v': 0.1, 'fake_state': 0}})

        # invalid predictor
        with self.assertRaises(Exception):
            session = prog_client.Session(pred='fake_pred')

        # invalid state est
        with self.assertRaises(Exception):
            session = prog_client.Session('ThrownObject', state_est = 'fake_est')

        # invalid predictor
        with self.assertRaises(Exception):
            session = prog_client.Session('ThrownObject', pred='fake_pred')

        # invalid load est
        with self.assertRaises(Exception):
            session = prog_client.Session('ThrownObject', load_est = 'fake_est')
        
        # Missing initial state
        with self.assertRaises(Exception):
            session = prog_client.Session('ThrownObject', x0 = {'x': 1.2})

        # Extra state
        x0 = {'x': 1.2, 'v': 2.3, 'max_y': 4.5}
        from prog_models.models import ThrownObject
        if 'max_x' in ThrownObject.states:
            # max_x was removed in recent version
            x0['max_x'] = 1.2
        with self.assertRaises(Exception):
            session = prog_client.Session('ThrownObject', x0 = x0)
    
    @classmethod
    def tearDownClass(cls):
        prog_server.stop()

        # Wait for shutdown to complete
        for i in range(TIMEOUT):
            if not prog_server.is_running():
                return
            time.sleep(1)

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
