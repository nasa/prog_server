# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

from .load_ests import build_load_est
from .prediction_handler import add_to_predict_queue

from flask import current_app as app
from flask import abort

from prog_models import models
from prog_algs import state_estimators, predictors
from threading import Lock

class Session():
    def __init__(self, session_id, 
            model_name, model_cfg = {}, x0 = None,
            state_est_name = 'ParticleFilter', state_est_cfg = {}, 
            load_est_name = 'MovingAverage', load_est_cfg = {},
            pred_name = 'MonteCarlo', pred_cfg = {}):
        
        # Save config
        self.session_id = session_id
        self.model_name = model_name
        self.state_est_name = state_est_name
        self.state_est_cfg = state_est_cfg
        self.load_est_name = load_est_name
        self.load_est_cfg = load_est_cfg
        self.pred_name = pred_name
        self.initialized = True
        self.results = None
        self.futures = [None, None]
        self.locks = {
            'estimate': Lock(),
            'execution': Lock(),
            'futures': Lock(),
            'results': Lock()
        }

        # Model
        try:
            model_class = getattr(models, model_name)
        except AttributeError:
            abort(400, f"Invalid model name {model_name}")

        app.logger.debug(f"Creating Model of type {model_name}")
        try:
            self.model = model_class(**model_cfg)
        except Exception as e:
            abort(400, f"Could not instantiate model with input: {e}")
        self.model_cfg = self.model.parameters.data
        self.moving_avg_loads = {key : [] for key in self.model.inputs}

        # Load Estimator
        self.set_load_estimator(load_est_name, load_est_cfg, predict_queue = False)

        # Initial State
        if x0 is None:
            # If initial state not provided, try initializing model without data
            try:
                x0 = self.model.initialize()
                app.logger.debug("Model initialized without data")
            except TypeError:
                # Model requires data to initialize. Must be initialized later
                app.logger.debug("Model cannot be initialized without data")
                self.initialized = False  
        else:
            self.set_state(x0)

        # Predictor
        try:
            pred_class = getattr(predictors, pred_name)
        except AttributeError:
            abort(400, f"Invalid predictor name {pred_name}")
        app.logger.debug(f"Creating Predictor of type {self.pred_name}")
        try:
            self.pred = pred_class(self.model, **pred_cfg)
        except Exception as e:
            abort(400, f"Could not instantiate predictor with input: {e}")
        self.pred_cfg = self.pred.parameters
        
        # State Estimator
        if self.initialized:
            # If state is initialized, then state estimator and predictor can be created without data
            self.__initialize(x0)
        else:
            # Otherwise, will have to be initialized later
            # Check state estimator and predictor data
            try:
                getattr(state_estimators, state_est_name)
            except AttributeError:  
                abort(400, f"Invalid state estimator name {state_est_name}")

    def __initialize(self, x0, predict_queue = True):
        app.logger.debug("Initializing...")
        state_est_class = getattr(state_estimators, self.state_est_name)
        app.logger.debug(f"Creating State Estimator of type {self.state_est_name}")
        if set(self.model.states) != set(list(x0.keys())):
            abort(400, f"Initial state must have every state in model. states. Had {list(x0.keys())}, needed {self.model.states}")

        try:
            self.state_est = state_est_class(self.model, x0, **self.state_est_cfg)
        except Exception as e:
            abort(400, f"Could not instantiate state estimator with input: {e}")

        self.initialized = True
        if predict_queue:
            add_to_predict_queue(self)

    def set_state(self, x):
        app.logger.debug(f"Setting state to {x}")
        # Initializes (or re-initializes) state estimator
        self.__initialize(x)

    def set_load_estimator(self, name, cfg, predict_queue = True):
        app.logger.debug(f"Setting load estimator to {name}")
        self.load_est_name = name
        self.load_est_cfg = cfg
        self.load_est = build_load_est(name, cfg, self)
        if predict_queue:
            add_to_predict_queue(self)

    def add_data(self, time, inputs, outputs):
        # Add data to state estimator
        if not self.initialized:
            x0 = self.model.initialize(inputs, outputs)
            self.__initialize(x0)
        else:
            app.logger.debug("Adding data to state estimator")
            with self.locks['estimate']:
                self.state_est.estimate(time, inputs, outputs)
            add_to_predict_queue(self)
    
    def to_dict(self):
        return {
            'session_id': self.session_id,
            'model': {
                'type': self.model_name,
                'cfg': self.model_cfg },
            'state_estimator': {
                'type': self.state_est_name,
                'cfg': self.state_est_cfg },
            'load_estimator': {
                'type': self.load_est_name,
                'cfg': self.load_est_cfg },
            'predictor': {
                'type': self.pred_name,
                'cfg': self.pred_cfg },
            'initialized': self.initialized
        }
