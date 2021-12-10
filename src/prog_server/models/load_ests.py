# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

from statistics import mean
from numpy.random import normal
from flask import abort
from functools import partial

def Variable(t, x = None, session = None, cfg = None):
    for time in cfg.keys():
        if t > float(time):
            return cfg[time]

def Const(t, x = None, session = None, cfg = None):
    return cfg['load']

def MovingAverage(t, x=None, session = None, cfg = None):
    std = cfg['base_std'] + cfg['std_slope'] * (t - cfg['t'])
    load = {key : mean(session.moving_avg_loads[key]) for key in session.model.inputs} 
    return {key : normal(load[key], std) for key in load.keys()}

def update_moving_avg(u, session = None, cfg = {'window_size': 10}):
    for key in session.model.inputs:
        session.moving_avg_loads[key].append(u[key])
        if len(session.moving_avg_loads[key]) > cfg['window_size']:
            del session.moving_avg_loads[key][0]  # Remove first item

def build_load_est(name, cfg, session):
    if name not in globals():
        abort(400, f"{name} is not a valid load estimation method")
    load_est_fcn = globals()[name]
    return partial(load_est_fcn,
        loading = cfg,
        session = session)
