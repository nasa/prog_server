# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

from statistics import mean
from numpy.random import normal
from flask import abort
from functools import partial

def Variable(t, x = None, session = None, cfg = None):
    """Variable (i.e. piecewise) load estimator. The piecewise load function is defined in the load_est_cfg as ordered dictionary starting_time: load. 

    cfg: ordered dictionary starting_time: load. First key should always be 0
        e.g., {'0': {'u1': 0.1}, '100': {'u1': 0.2}, '300': {'u1': 0.3}, '500': {'u1': 0.0}}
    """
    for time in cfg.keys():
        if t > float(time):
            return cfg[time]

def Const(t, x = None, session = None, cfg = None):
    """Constant load estimator. Load is assumed to be constant over time. 

    cfg: dictionary with one key (load) where value is the constant load (dict)
        e.g., {'load': {'u1': 0.1}}
    """
    return cfg['load']

def MovingAverage(t, x=None, session = None, cfg = None):
    """Moving average load estimator. Load is estimated as the mean of the last `window_size` samples. Noise can be added using the following optional configuration parameters:

        * base_std: standard deviation of noise
        * std_slope: Increase in std with time (e.g., 0.1 = increase of 0.1 in std per second)
        * t0: Starting time for calculation of std

    std of applied noise is defined as base_std + std_slope (t-t0). By default no noise is added
    """
    std = cfg.get('base_std',0)  + cfg.get('std_slope', 0) * (t - cfg.get('t0', 0))
    load = {key : mean(session.moving_avg_loads[key]) for key in session.model.inputs} 
    return {key : normal(load[key], std) for key in load.keys()}

def update_moving_avg(u, session = None, cfg = {}):
    for key in session.model.inputs:
        session.moving_avg_loads[key].append(u[key])
        if len(session.moving_avg_loads[key]) > cfg.get('window_size', 10):
            del session.moving_avg_loads[key][0]  # Remove first item

def build_load_est(name, cfg, session):
    if name not in globals():
        abort(400, f"{name} is not a valid load estimation method")
    load_est_fcn = globals()[name]
    return partial(load_est_fcn,
        cfg = cfg,
        session = session)
