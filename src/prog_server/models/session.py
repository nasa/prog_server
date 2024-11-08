# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

from prog_server.models.load_ests import build_load_est
from prog_server.models.prediction_handler import add_to_predict_queue

from copy import deepcopy
from flask import current_app as app
from flask import abort
import json
from progpy import models, state_estimators, predictors, PrognosticsModel
from threading import Lock

extra_models = {}
extra_predictors = {}
extra_estimators = {}

class Session():
    def __init__(self, session_id,
            model_name, model_cfg={}, x0=None,
            state_est_name='ParticleFilter', state_est_cfg={},
            load_est_name='MovingAverage', load_est_cfg={},
            pred_name='MonteCarlo', pred_cfg={}):
        
        # Save config
        self.session_id = session_id
        self.model_name = model_name
        self.state_est_name = state_est_name
        self.state_est_cfg = state_est_cfg
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
            if model_name in extra_models:
                model_class = extra_models[model_name]
            else:
                model_class = getattr(models, model_name)
        except AttributeError:
            abort(400, f"Invalid model name {model_name}")

        app.logger.debug(f"Creating Model of type {model_name}")
        if isinstance(model_class, type) and issubclass(model_class, PrognosticsModel):
            # model_class is a class, either from progpy or custom classes
            try:
                self.model = model_class(**model_cfg)
            except Exception as e:
                abort(400, f"Could not instantiate model with input: {e}")
        elif isinstance(model_class, PrognosticsModel):
            # model_class is an instance of a PrognosticsModel- use the object instead
            # This happens for user models that are added to the server at startup.
            self.model = deepcopy(model_class)
            # Apply any configuration changes, overriding model config.
            self.model.parameters.update(model_cfg)
        else:
            abort(400, f"Invalid model type {type(model_name)} for model {model_name}. For custom classes, the model must be either an instantiated PrognosticsModel subclass or classmame")
        self.model_cfg = self.model.parameters
        self.moving_avg_loads = {key: [] for key in self.model.inputs}

        # Load Estimator
        self.set_load_estimator(load_est_name, load_est_cfg, predict_queue=False)

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
            if pred_name in extra_predictors:
                pred_class = extra_predictors[pred_name]
            else:
                pred_class = getattr(predictors, pred_name)
        except AttributeError:
            abort(400, f"Invalid predictor name {pred_name}")
        app.logger.debug(f"Creating Predictor of type {self.pred_name}")
        if isinstance(pred_class, type) and issubclass(pred_class, predictors.Predictor):
            # pred_class is a class, either from progpy or custom classes
            try:
                self.pred = pred_class(self.model, **pred_cfg)
            except Exception as e:
                abort(400, f"Could not instantiate predictor with input: {e}")
        elif isinstance(pred_class, predictors.Predictor):
            # pred_class is an instance of predictors.Predictor - use the object instead
            # This happens for user predictors that are added to the server at startup.
            self.pred = deepcopy(pred_class)
            # Apply any configuration changes, overriding predictor config.
            self.pred.parameters.update(pred_cfg)
        else:
            abort(400, f"Invalid predictor type {type(pred_name)} for predictor {pred_name}. For custom classes, the predictor must be mentioned with quotes in the pred argument")
            
        self.pred_cfg = self.pred.parameters
        
        # State Estimator
        if self.initialized:
            # If state is initialized, then state estimator and predictor can
            # be created without data
            self.__initialize(x0)
        else:
            # Otherwise, will have to be initialized later
            # Check state estimator and predictor data
            try:
                if self.state_est_name not in extra_estimators:
                    getattr(state_estimators, state_est_name)
            except AttributeError:  
                abort(400, f"Invalid state estimator name {state_est_name}")

    def __initialize(self, x0, predict_queue=True):
        app.logger.debug("Initializing...")
        #Estimator
        try:
            if self.state_est_name in extra_estimators:
                state_est_class = extra_estimators[self.state_est_name]
            else:
                state_est_class = getattr(state_estimators, self.state_est_name)
        except AttributeError:
            abort(400, f"Invalid state estimator name {self.state_est_name}")
        app.logger.debug(f"Creating State Estimator of type {self.state_est_name}")

        if isinstance(x0, str):
            x0 = json.loads(x0) #loads the initial state
        if set(self.model.states) != set(list(x0.keys())):
            abort(400, f"Initial state must have every state in model. states. Had {list(x0.keys())}, needed {self.model.states}")
            
        if isinstance(state_est_class, type) and issubclass(state_est_class, state_estimators.StateEstimator):
            try:
                self.state_est = state_est_class(self.model, x0, **self.state_est_cfg)
            except Exception as e:
                abort(400, f"Could not instantiate state estimator with input: {e}")
        elif isinstance(state_est_class, state_estimators.StateEstimator):
            # state_est_class is an instance of state_estimators.StateEstimator - use the object instead
            # This happens for user state estimators that are added to the server at startup.
            self.state_est = deepcopy(state_est_class)
            # Apply any configuration changes, overriding estimator config
            self.state_est.parameters.update(self.state_est_cfg)
        else:
            abort(400, f"Invalid state estimator type {type(self.state_est_name)} for estimator {self.state_est_name}. For custom classes, the state estimator must be mentioned with quotes in the est argument")

        self.initialized = True
        if predict_queue:
            add_to_predict_queue(self)

    def set_state(self, x):
        app.logger.debug(f"Setting state to {x}")
        # Initializes (or re-initializes) state estimator
        self.__initialize(x)

    def set_load_estimator(self, name, cfg, predict_queue=True):
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
                'cfg': self.model_cfg.to_json()},
            'state_estimator': {
                'type': self.state_est_name,
                'cfg': self.state_est_cfg},
            'load_estimator': {
                'type': self.load_est_name,
                'cfg': self.load_est_cfg},
            'predictor': {
                'type': self.pred_name,
                'cfg': self.pred_cfg},
            'initialized': self.initialized
        }
