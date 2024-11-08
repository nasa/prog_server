# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

import requests, json
import urllib3
import pickle
from progpy.uncertain_data import UncertainData
from progpy.utils import containers

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Session:
    """
    Create a new Session in `prog_server`

    Args:
        model (str): The model to use for this session (e.g., batt)
        host (str, optional): Host address for PaaS Service. Defaults to '127.0.0.1'
        port (int, optional): Port for PaaS Service. Defaults to 5000.
        model_cfg (dict, optional): Configuration for ProgModel.
        x0 (dict, optional): Initial state for ProgModel.
        load_est (str, optional): Load estimator to use.
        load_est_cfg (dict, optional): Configuration for load estimator.
        state_est (str, optional): State Estimator to use (e.g., ParticleFilter). Class name for state estimator in `progpy.state_estimators`
        state_est_cfg (dict, optional): Configuration for state estimator.
        pred (str, optional): Prediction algorithm to use (e.g., MonteCarlo). Class name for prediction algorithm in `progpy.predictors`
        pred_cfg (dict, optional): Configuration for prediction algorithm.

    Use:
        session = prog_client.Session(**config)
    """

    _base_url = '/api/v1'
    def __init__(self, model, host = '127.0.0.1', port=8555, **kwargs):
        self.host = 'http://' + host + ':' + str(port) + Session._base_url

        # Process kwargs with json value
        for key, value in kwargs.items():
            if isinstance(value, dict) or isinstance(value, list):
                kwargs[key] = json.dumps(value)
        
        # Start session
        result = requests.put(self.host + '/session', data={'model': model, **kwargs})

        # If error code throw Exception
        if result.status_code != 201:
            raise Exception(result.text)
        
        # Load information
        self.session_id = json.loads(result.text)['session_id']
        self.host += "/session/" + str(self.session_id)

    def __str__(self):
        return f'PaaS Session {self.session_id}'

    def is_init(self):
        """Check if session has been initialized

        Returns:
            bool: If the session has been initialized
        """
        result = requests.get(self.host + '/initialized')
        return json.loads(result.text)['initialized']

    def send_data(self, time, **kwargs):
        """Send data to service

        Args:
            time (float): Time for data point
            ... Other arguments as keywords

        Example:
            session.send_data(10.2, t=32.0, v=3.914, i=2)
        """
        result = requests.post(self.host + '/data', data={'time': time, **kwargs})

        # If error code throw Exception
        if result.status_code != 204:
            raise Exception(result.text)

    def send_loading(self, type: str, cfg: dict):
        """
        Set the future loading profile profile. 

        Args:
            type (str): Type of loading profile
            cfg (dict): Configuration of loading profile
        """
        result = requests.post(self.host + '/loading', data={'type': type, 'cfg': json.dumps(cfg)})
        
        # If error code throw Exception
        if result.status_code != 204:
            raise Exception(result.text)

    def set_state(self, x):
        """
        Set the model state.

        Args:
            x (UncertainData, Dict, model.StateContainer): Model state
        """
        if isinstance(x, UncertainData):
            x = pickle.dumps(x)
            input_format = 'uncertain_data'
        elif isinstance(x, containers.DictLikeMatrixWrapper):
            x = pickle.dumps(x)
            input_format = 'state_container'
        elif isinstance(x, dict):
            x = {'x': json.dumps(x)}
            input_format = 'dict'
        else:
            raise Exception('Invalid state type ' + str(type(x)))

        result = requests.post(self.host + '/state', data=x, params={'format': input_format})

        # If error code throw Exception
        if result.status_code != 204:
            raise Exception(result.text)

    def get_state(self):
        """Get the model state 

        Returns:
            tuple: \\
                | float: Time of state estimate
                | UncertainData: Model state
        """
        result = requests.get(self.host + '/state', params={'return_format': 'uncertain_data'}, stream='True')

        # If error code throw Exception
        if result.status_code != 200:
            raise Exception(result.text)

        result = pickle.load(result.raw)
        return (result['time'], result['state'])

    def get_output(self):
        """Get the model output 

        Returns:
            tuple: \\
                | float: Time of state estimate
                | UncertainData: Model state
        """
        result = requests.get(self.host + '/output', params={'return_format': 'uncertain_data'}, stream='True')

        # If error code throw Exception
        if result.status_code != 200:
            raise Exception(result.text)

        result = pickle.load(result.raw)
        return (result['time'], result['output'])

    def get_predicted_state(self):
        """Get the predicted model state 

        Returns:
            tuple: \\
                | float: Time of prediction
                | Prediction: Predicted model state at save points
        """
        result = requests.get(self.host + '/prediction/state', params={'return_format': 'uncertain_data'}, stream='True')

        # If error code throw Exception
        if result.status_code != 200:
            raise Exception(result.text)

        result = pickle.load(result.raw)
        return (result['prediction_time'], result['states'])

    def get_event_state(self):
        """Get the current event state

        Returns:
            tuple: \\
                | float: Time of state estimate
                | UncertainData: Event state
        """
        result = requests.get(self.host + '/event_state', params={'return_format': 'uncertain_data'}, stream='True')

        # If error code throw Exception
        if result.status_code != 200:
            raise Exception(result.text)

        result = pickle.load(result.raw)
        return (result['time'], result['event_state'])

    def get_predicted_output(self):
        """Get the predicted output

        Returns:
            tuple: \\
                | float: Time of prediction
                | Prediction: predicted Event state
        """
        result = requests.get(self.host + '/prediction/output', params={'return_format': 'uncertain_data'}, stream='True')

        # If error code throw Exception
        if result.status_code != 200:
            raise Exception(result.text)

        result = pickle.load(result.raw)
        return (result['prediction_time'], result['outputs'])

    def get_predicted_event_state(self):
        """Get the predicted event state

        Returns:
            tuple: \\
                | float: Time of prediction
                | Prediction: predicted Event state
        """
        result = requests.get(self.host + '/prediction/event_state', params={'return_format': 'uncertain_data'}, stream='True')

        # If error code throw Exception
        if result.status_code != 200:
            raise Exception(result.text)

        result = pickle.load(result.raw)
        return (result['prediction_time'], result['event_states'])

    def get_predicted_toe(self):
        """Get the predicted Time of Event (ToE)

        Returns:
            tuple: \\
                | float: Time of prediction
                | UncertainData: Prediction

        See also: get_prediction_status
        """
        result = requests.get(self.host + '/prediction/events', params={'return_format': 'uncertain_data'}, stream='True')

        # If error code throw Exception
        if result.status_code != 200:
            raise Exception(result.text)
            
        result = pickle.load(result.raw)
        return (result['prediction_time'], result['time_of_event'])

    def get_prediction_status(self):
        """Get the status of the prediction

        Returns:
            dict: Status of prediction 
        """
        result = requests.get(self.host + '/prediction/status')

        # If error code throw Exception
        if result.status_code != 200:
            raise Exception(result.text)

        return json.loads(result.text)

    def get_performance_metrics(self):
        """Get current performance metrics

        Returns:
            tuple: \\
                | float: Time of state estimate
                | UncertainData: Performance Metrics
        """
        result = requests.get(self.host + '/performance_metrics', params={'return_format': 'uncertain_data'}, stream='True')

        # If error code throw Exception
        if result.status_code != 200:
            raise Exception(result.text)

        result = pickle.load(result.raw)
        return (result['time'], result['performance_metrics'])

    def get_predicted_performance_metrics(self):
        """Get predicted performance metrics

        Returns:
            tuple: \\
                | float: Time of prediction
                | Prediction: Predicted performance Metrics
        """
        result = requests.get(self.host + '/prediction/performance_metrics', params={'return_format': 'uncertain_data'}, stream='True')

        # If error code throw Exception
        if result.status_code != 200:
            raise Exception(result.text)

        result = pickle.load(result.raw)
        return (result['prediction_time'], result['performance_metrics'])
    
    def get_model(self):
        """
        Get the configured PrognosticsModel used by the session

        Returns:
            PrognosticsModel: configured PrognosticsModel used by the session

        Example:
            m = session.get_model()
        """
        result = requests.get(self.host + '/model', params={'return_format': 'pickle'}, stream='True')

        # If error code throw Exception
        if result.status_code != 200:
            raise Exception(result.text)

        return pickle.load(result.raw)
