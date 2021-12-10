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
        self.model_cfg = model_cfg
        self.state_est_name = state_est_name
        self.state_est_cfg = state_est_cfg
        self.load_est_name = load_est_name
        self.load_est_cfg = load_est_cfg
        self.pred_name = pred_name
        self.pred_cfg = pred_cfg
        self.initialized = True
        self.results = None
        self.futures = [None, None],
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
        self.model = model_class(**model_cfg)
        self.moving_avg_loads = {key : [] for key in self.model.inputs},

        # Load Estimator
        self.set_load_estimator(load_est_name, load_est_cfg)

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

        # Predictor
        try:
            pred_class = getattr(predictors, pred_name)
        except AttributeError:
            abort(400, f"Invalid predictor name {pred_name}")
        app.logger.debug(f"Creating Predictor of type {self.pred_name}")
        self.predictor = pred_class(self.model, **pred_cfg)

    def __initialize(self, x0):
        state_est_class = getattr(state_estimators, self.state_est_name)
        app.logger.debug(f"Creating State Estimator of type {self.state_est_name}")
        self.state_est = state_est_class(self.model, x0, **self.state_est_cfg)

        self.initialized = True

    @property
    def state(self):
        pass # TODO(CT): GET STATE

    def set_state(self, x):
        # Initializes (or re-initializes) state estimator
        self.__initialize(x)

    def set_load_estimator(self, name, cfg):
        self.load_est_name = name
        self.load_est_cfg = cfg
        self.load_est = build_load_est(name, cfg, self)

    def add_data(self, time, inputs, outputs):
        # Add data to state estimator
        if not self.initialized:
            x0 = self.model.initialize(inputs, outputs)
            self.__initialize(x0)
        else:
            with self.locks['estimate']:
                self.state_est.estimate(time, inputs, outputs)
    
    def to_dict(self):
        return {
            'session_id': self.session_id,
            'model': self.model_name,
            'state_estimator': self.state_est_name,
            'load_estimator': self.load_est_name,
            'predictor': self.pred_name,
            'initialized': self.initialized
        }
