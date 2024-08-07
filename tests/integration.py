# Copyright © 2021 United States Government as represented by the Administrator of the National Aeronautics and Space Administration. All Rights Reserved.

import time
import unittest
import numpy as np
import prog_client, prog_server
from progpy import PrognosticsModel
from progpy.predictors import MonteCarlo
from progpy.uncertain_data import MultivariateNormalDist
from progpy.models import ThrownObject
from progpy.models.thrown_object import LinearThrownObject
from progpy.state_estimators import KalmanFilter
from progpy.state_estimators import ParticleFilter
from progpy.uncertain_data import MultivariateNormalDist
from progpy.uncertain_data import UnweightedSamples


class IntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        prog_server.start()

    def test_integration(self):
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

        x2 = {'x': 1, 'v': 20}
        session.set_state(x2)
        (_, x) = session.get_state()
        for key, value in x.mean.items():
            self.assertAlmostEqual(value, x2[key])

        mean = {'x': 2, 'v': 40}
        cov = [[0.1, 0], [0, 0.1]]
        x3 = MultivariateNormalDist(mean.keys(), list(mean.values()), cov)
        session.set_state(x3)
        (_, x) = session.get_state()
        for key, value in x.mean.items():
            self.assertAlmostEqual(value, mean[key], delta=0.5)
        for i in range(len(x0)):
            for j in range(len(x0)):
                self.assertAlmostEqual(x.cov[i][j], cov[i][j], delta=0.1)
        
        # Reset State - state container
        session.set_state(x0)
        (_, x) = session.get_state()
        for key, value in x.mean.items():
            self.assertAlmostEqual(value, x0[key])
        
        # Event State
        (_, es) = session.get_event_state()
        es0 = m.event_state(x0)
        for key, value in es.mean.items():
            self.assertAlmostEqual(value, es0[key])

        # Output
        (_, z) = session.get_output()
        z0 = m.output(x0)
        for key, value in z.mean.items():
            self.assertAlmostEqual(value, z0[key])

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
        self.assertAlmostEqual(ToE.mean['falling'], 3.8, delta=0.1)
        self.assertAlmostEqual(ToE.mean['impact'], 7.9, delta=0.1)

        # Prep Prediction
        (times, _, sim_states, sim_z, sim_es) = m.simulate_to_threshold(lambda t,x=None: {}, threshold_keys='impact', save_freq=0.1, dt=0.1)

        # Prediction - future states
        (t_p, states) = session.get_predicted_state()
        self.assertAlmostEqual(t_p, -1e-99)

        for i in range(len(states.times)):
            self.assertAlmostEqual(states.times[i], i/10, delta=0.2)
            for key, value in states.snapshot(i).mean.items():
                if i < len(sim_states):  # may have one or two more states
                    self.assertAlmostEqual(value, sim_states[i][key], delta = (i+1)/15, msg=f"snapshot at {i/10}s for key {key} should be {sim_states[i][key]} was {value}")

        # Prediction - future outputs
        (t_p, outputs) = session.get_predicted_output()
        self.assertAlmostEqual(t_p, -1e-99)

        for i in range(len(outputs.times)):
            self.assertAlmostEqual(outputs.times[i], i/10, delta=0.2)
            for key, value in outputs.snapshot(i).mean.items():
                if i < len(sim_z):  # may have one or two more states
                    self.assertAlmostEqual(value, sim_z[i][key], delta=(i+1)/20, msg=f"snapshot at {i/10}s for key {key} should be {sim_z[i][key]} was {value}")

        # Prediction - future event_states
        (t_p, states) = session.get_predicted_event_state()
        self.assertAlmostEqual(t_p, -1e-99)

        for i in range(len(states.times)):
            self.assertAlmostEqual(states.times[i], i/10, delta=0.2)
            for key, value in states.snapshot(i).mean.items():
                if i < len(sim_es):  # may have one or two more states
                    self.assertAlmostEqual(value, sim_es[i][key], delta=(i+1)/20, msg=f"snapshot at {i/10}s for key {key} should be {sim_es[i][key]} was {value}")

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

    def test_dt(self):
        # Set dt to 1 and save_freq to 0.1
        session_point1 = prog_client.Session(
            'ThrownObject',
            pred_cfg={'save_freq': 0.1, 'dt':0.1})
        session_1 = prog_client.Session(
            'ThrownObject',
            pred_cfg={'save_freq': 0.1, 'dt':1})

        for _ in range(5):
            # Wait for prediction to complete
            time.sleep(0.5)
            status = session_1.get_prediction_status()
            if status['last prediction'] is not None:
                break

        for _ in range(5):
            # Wait for prediction to complete
            time.sleep(0.5)
            status = session_point1.get_prediction_status()
            if status['last prediction'] is not None:
                break
        
        result_point1 = session_point1.get_predicted_event_state()
        result_1 = session_1.get_predicted_event_state()
        self.assertEqual(len(result_1[1][1].times), 9)
        self.assertEqual(len(result_point1[1][1].times), 79)

        # result_1 is less, despite having the same save_freq,
        # because the time step is 1,
        # so it can't save as frequently

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
            session = prog_client.Session('ThrownObject', state_est='fake_est')

        # invalid predictor
        with self.assertRaises(Exception):
            session = prog_client.Session('ThrownObject', pred='fake_pred')

        # invalid load est
        with self.assertRaises(Exception):
            session = prog_client.Session('ThrownObject', load_est='fake_est')
        
        # Missing initial state
        with self.assertRaises(Exception):
            session = prog_client.Session('ThrownObject', x0={'x': 1.2})

        # Extra state
        x0 = {'x': 1.2, 'v': 2.3, 'max_y': 4.5}
        if 'max_x' in ThrownObject.states:
            # max_x was removed in recent version
            x0['max_x'] = 1.2
        with self.assertRaises(Exception):
            session = prog_client.Session('ThrownObject', x0=x0)

    def test_custom_models(self):
        # Restart server with model
        prog_server.stop()
        ball = ThrownObject(thrower_height=1.5, throwing_speed=20)
        prog_server.start(models={'ball': ball}, port=9883)
        ball_session = prog_client.Session('ball', port=9883)

        # Check initial state - should equal model state
        t, x = ball_session.get_state()
        gt_mean = ball.initialize()
        x_mean = x.mean
        self.assertEqual(x_mean['x'], gt_mean['x'])
        self.assertEqual(x_mean['v'], gt_mean['v'])

        # Iterate forward 1 second and compare
        gt_mean = ball.next_state(gt_mean, None, 1)
        ball_session.send_data(time=1, x=gt_mean['x'])
        t, x = ball_session.get_state()
        x_mean = x.mean
        self.assertEqual(x_mean['x'], gt_mean['x'])
        self.assertEqual(x_mean['v'], gt_mean['v'])
        
        # Restart (to reset port)
        prog_server.stop()
        prog_server.start()


        # Later (not yet supported) repeat test model class
        # class TestModel(PrognosticsModel):
        #     inputs = ['u']
        #     states =  ['x']
        #     outputs = ['x+1']

        #     default_parameters = {
        #         'x0': {
        #             'x': 0
        #         }
        #     }

        #     def next_state(self, x, u, dt):
        #         x['x'] = u['u']
        #         return x

        #     def output(self, x):
        #         return self.OutputContainer({'x+1': x['x']+1})

        # prog_server.start(models={'test': TestModel})
        # test_session = prog_client.Session('TestModel')

        # # Check initial state - should equal model state
        # z = test_session.get_output()
        # self.assertEqual(z['x+1'], 1)

        # # Iterate forward 1 second and compare
        # test_session.send_data(time=1, u=5)
        # z = test_session.get_output()
        # self.assertEqual(z['x+1'], 6)

    @classmethod
    def tearDownClass(cls):
        prog_server.stop()

    def test_custom_predictors(self):
        # Restart server with model
        prog_server.stop()
        #define the model
        ball = ThrownObject(thrower_height=1.5, throwing_speed=20)
        #call the external/extra predictor (here from progpy)
        mc = MonteCarlo(ball)
        with self.assertRaises(Exception):
            prog_server.start(port=9883, predictors=[1, 2])

        prog_server.start(port=9883, predictors={'mc':mc})
        ball_session = prog_client.Session('ThrownObject', port=9883, pred='mc')
        
        #check that the prediction completes successfully without error
        #get_prediction_status from the session - for errors
        sessions_in_progress = True
        STEP = 15  # Time to wait between pinging server (s)
        while sessions_in_progress:
            sessions_in_progress = False
            status = ball_session.get_prediction_status()
            if status['in progress'] != 0:
                print(f'\tSession {ball_session.session_id} is still in progress')
                sessions_in_progress = True
                time.sleep(STEP)
        print(f'\tSession {ball_session.session_id} complete')
        print(status)
        # Restart (to reset port)
        prog_server.stop()
        prog_server.start()

    def test_custom_estimators(self):
        # Restart server with model
        prog_server.stop()

        #define the custom model
        ball = LinearThrownObject(thrower_height=1.5, throwing_speed=20)
        x_guess = ball.StateContainer({'x': 1.75, 'v': 35})
        kf = KalmanFilter(ball, x_guess)
        prog_server.start(models ={'ball':ball}, port=9883, state_estimators={'kf':kf})
        ball_session = prog_client.Session('ball', port=9883, state_est='kf')

        # time step (s)
        dt = 0.01 
        x = ball.initialize()
        # Initial input 
        u = ball.InputContainer({})  

        # Iterate forward 1 second and compare
        x = ball.next_state(x, u, 1) 
        ball_session.send_data(time=1, x=x['x'])

        t, x_s = ball_session.get_state()

        # To check if the output state is multivariate normal distribution
        self.assertIsInstance(x_s, MultivariateNormalDist)
      
        # Setup Particle Filter
        pf = ParticleFilter(ball, x_guess)
        prog_server.stop()
        prog_server.start(models ={'ball':ball}, port=9883, state_estimators={'pf': pf, 'kf':kf})
        ball_session = prog_client.Session('ball', port=9883, state_est='pf')
        
        # Iterate forward 1 second and compare
        x = ball.next_state(x, u, 1) 
        ball_session.send_data(time=1, x=x['x'])
        
        t, x_s = ball_session.get_state()

        # Ensure that PF output is unweighted samples
        self.assertIsInstance(x_s, UnweightedSamples)
       
        prog_server.stop()
        prog_server.start()


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
