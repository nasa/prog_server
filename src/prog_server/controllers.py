# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

from numpy import cov
from .models.session import Session
from .models.load_ests import update_moving_avg
from prog_models.sim_result import SimResult, LazySimResult
from prog_algs.uncertain_data import UnweightedSamples
from prog_algs.predictors import Prediction, UnweightedSamplesPrediction
from flask import request, abort, jsonify
from flask import current_app as app
import json
from concurrent.futures._base import TimeoutError
import pickle

session_count = 0
sessions = {}

def api_v1():
    return jsonify({'message': 'Welcome to the PaaS Sandbox API!'})

# Session
def new_session():
    """
    Create a new session.

    Args:

    """
    global session_count
    app.logger.debug("Creating New Session")

    if 'model' not in request.form:
        abort(400, 'model must be specified in request body')

    model_name = request.form['model'] # Replace with actual type name

    session_id = session_count
    session_count += 1

    try: 
        model_cfg = json.loads(request.form.get('model_cfg', '{}'))
    except json.decoder.JSONDecodeError:
        abort(400, 'model_cfg must be valid JSON')

    try:
        load_est_cfg = json.loads(request.form.get('load_est_cfg', '{}'))
    except json.decoder.JSONDecodeError:
        abort(400, 'load_est_cfg must be valid JSON')

    try:
        pred_cfg = json.loads(request.form.get('pred_cfg', '{}'))
    except json.decoder.JSONDecodeError:
        abort(400, 'pred_cfg must be valid JSON')

    try:
        state_est_cfg = json.loads(request.form.get('state_est_cfg', '{}'))
    except json.decoder.JSONDecodeError:
        abort(400, 'state_est_cfg must be valid JSON')

    sessions[session_id] = Session(session_id, model_name,
        model_cfg = model_cfg,
        x0 = request.form.get('x0', None),
        state_est_name = request.form.get('state_est', 'ParticleFilter'),
        state_est_cfg = state_est_cfg,
        load_est_name = request.form.get('load_est', 'MovingAverage'),
        load_est_cfg = load_est_cfg,
        pred_name = request.form.get('pred', 'MonteCarlo'),
        pred_cfg = pred_cfg
    )
    
    return jsonify(sessions[session_id].to_dict()), 201

def get_sessions():
    """
    Get the sessions.

    Returns:
        The sessions.
    """
    app.logger.debug("Getting Active Sessions")
    return jsonify({'sessions': list(sessions.keys())})

def get_session(session_id):
    """
    Get the session.

    Args:
        session_id: The session ID.

    Returns:
        The session.
    """
    if session_id not in sessions:
        abort(400, f'Session {session_id} does not exist or has ended')

    app.logger.debug(f"Getting details for Session {session_id}")

    return jsonify(sessions[session_id].to_dict())

def delete_session(session_id):
    """
    Delete the session.

    Args:
        session_id: The session ID.
    """
    if session_id not in sessions:
        abort(400, f'Session {session_id} does not exist or has ended')

    app.logger.debug(f"Ending Session {session_id}")
    del sessions[session_id]
    return jsonify({'id': session_id, 'status': 'stopped'})

# Set
def set_state(session_id):
    """
    Set the system state for the session's model.

    Args:
        session_id: The session ID.
        state: The new state.
    """
    if session_id not in sessions:
        abort(400, f'Session {session_id} does not exist or has ended')

    if 'x' not in request.form:
        abort(400, "state ('x') must be specified in request body")

    app.logger.debug(f"Setting state for Session {session_id}")
    x = request.form.get('x')
    
    sessions[session_id].set_state(x)

    return '', 204

def set_loading_profile(session_id):
    """
    Set the loading profile for the session's model.

    Args:
        session_id: The session ID.
    """
    if session_id not in sessions:
        abort(400, f'Session {session_id} does not exist or has ended')

    app.logger.debug(f"Setting loading profile for Session {session_id}")

    try:
        load_est_cfg = json.loads(request.form.get('cfg', '{}'))
    except json.decoder.JSONDecodeError:
        abort(400, 'cfg must be valid JSON')

    sessions[session_id].set_load_estimator(
        request.values['type'], 
        load_est_cfg)

    return get_loading_profile(session_id)

def send_data(session_id):
    """
    Send data to the session's model.

    Args:
        session_id: The session ID.
        data: The data to send.
    """
    if session_id not in sessions:
        abort(400, f'Session {session_id} does not exist or has ended')

    app.logger.debug(f"Data received from session {session_id}")
    values = request.form
    session = sessions[session_id]

    try:
        inputs = {key : float(values[key]) for key in session.model.inputs}
        outputs = {key : float(values[key]) for key in session.model.outputs}
        time = float(values['time'])
    except KeyError:
        abort(400, f'Data missing for session {session_id}. Expected inputs: {session.model.inputs} and outputs: {session.model.outputs}. Received {list(values.keys())}')

    # Update moving average
    update_moving_avg(inputs, session, session.load_est_cfg)

    session.add_data(time, inputs, outputs)

    return '', 204

# Get
def get_loading_profile(session_id):
    """
    Get the loading profile for the session's model.

    Args:
        session_id: The session ID.

    Returns:
        The loading profile of the session.
    """
    if session_id not in sessions:
        abort(400, f'Session {session_id} does not exist or has ended')

    return jsonify({
        'type': sessions[session_id].load_est_name, 
        'cfg': sessions[session_id].load_est_cfg})

def get_initialized(session_id):
    """
    Get the initialized state for the session's model.

    Args:
        session_id: The session ID.

    Returns:
        The initialized state of the session.
    """
    if session_id not in sessions:
        abort(400, f'Session {session_id} does not exist or has ended')

    return jsonify({'initialized': sessions[session_id].initialized})

def get_prediction_status(session_id):
    """
    Get the prediction status for the session's model.

    Args:
        session_id: The session ID.

    Returns:
        The prediction status of the session.
    """
    if session_id not in sessions:
        abort(400, f'Session {session_id} does not exist or has ended')
    if not sessions[session_id].initialized:
        abort(400, 'Model not initialized')

    app.logger.debug(f"Getting prediction status for Session {session_id}")

    status = {
        'exceptions': [],
        'in progress': 0,
        'last prediction': None
    }

    with sessions[session_id].locks['futures']:
        for future in sessions[session_id].futures:
            if future is not None:
                try:
                    except_msg = str(future.exception(timeout = 0))
                    if except_msg != "None":
                        status['exceptions'].append(except_msg)
                except TimeoutError:
                    # Timeout Error = No error in thread (request for exceptions timed out)
                    pass
                status['in progress'] += future.running()
    with sessions[session_id].locks['results']:
        if sessions[session_id].results is not None: 
            status['last prediction'] = sessions[session_id].results[0].strftime("%c")
    return jsonify(status)  

# Get current
def get_state(session_id):
    """
    Get the system state for the session's model.

    Args:
        session_id: The session ID.

    Returns:
        The state of the session.
    """
    if session_id not in sessions:
        abort(400, f'Session {session_id} does not exist or has ended')
    if not sessions[session_id].initialized:
        abort(400, 'Model not initialized')

    mode = request.args.get('return_format', 'mean')
    
    app.logger.debug(f"Getting state for Session {session_id}. Return mode: {mode}")
    with sessions[session_id].locks['estimate']:
        if mode == 'mean':
            state = sessions[session_id].state_est.x.mean
        elif mode == 'metrics':
            state = sessions[session_id].state_est.x.metrics()
        elif mode == 'multivariate_norm':
            state = {

                    'mean': sessions[session_id].state_est.x.mean,
                    'cov': sessions[session_id].state_est.x.cov.tolist(),
                }
        elif mode == 'uncertain_data':
            return pickle.dumps({
                "time": sessions[session_id].state_est.t,
                "state": sessions[session_id].state_est.x
                })
        else:
            abort(400, f'Invalid return mode: {mode}')
        return jsonify({
            "time": sessions[session_id].state_est.t,
            "state": state})

def get_event_state(session_id):
    """
    Get the event state for the session's model.

    Args:
        session_id: The session ID.

    Returns:
        The event state of the session.
    """
    if session_id not in sessions:
        abort(400, f'Session {session_id} does not exist or has ended')
    if not sessions[session_id].initialized:
        abort(400, 'Model not initialized')

    mode = request.args.get('return_format', 'mean')

    app.logger.debug(f"Getting event state for Session {session_id}. Return mode: {mode}")
    with sessions[session_id].locks['estimate']:
        if mode == 'mean':
            x = sessions[session_id].state_est.x.mean
            es = sessions[session_id].model.event_state(x)
        elif mode == 'metrics':
            x = sessions[session_id].state_est.x.sample(100)
            es = UnweightedSamples([sessions[session_id].model.event_state(x_) for x_ in x])
            es = es.metrics()
        elif mode == 'multivariate_norm':
            x = sessions[session_id].state_est.x.sample(100)
            es = UnweightedSamples([sessions[session_id].model.event_state(x_) for x_ in x])
            es = {
                    'mean': es.mean,
                    'cov': es.cov.tolist()
                }
        elif mode == 'uncertain_data':
            x = sessions[session_id].state_est.x.sample(100)
            es = UnweightedSamples([sessions[session_id].model.event_state(x_) for x_ in x])
            return pickle.dumps({
                "time": sessions[session_id].state_est.t,
                "event_state": es})
        else:
            abort(400, f'Invalid return mode: {mode}')

        return jsonify({
            "time": sessions[session_id].state_est.t,
            "event_state": es})

def get_perf_metrics(session_id):
    """
    Get the performance metrics for the session's model.

    Args:
        session_id: The session ID.

    Returns:
        The performance metrics of the session.
    """
    if session_id not in sessions:
        abort(400, f'Session {session_id} does not exist or has ended')
    if not sessions[session_id].initialized:
        abort(400, 'Model not initialized')

    mode = request.args.get('return_format', 'mean')
    app.logger.debug(f"Getting Performance Metrics for Session {session_id}")

    with sessions[session_id].locks['estimate']:
        if mode == 'mean':
            x = sessions[session_id].state_est.x.mean
            pm = sessions[session_id].model.observables(x)
        elif mode == 'metrics':
            x = sessions[session_id].state_est.x.sample(100)
            es = UnweightedSamples([sessions[session_id].model.observables(x_) for x_ in x])
            pm = es.metrics()
        elif mode == 'multivariate_norm':
            x = sessions[session_id].state_est.x.sample(100)
            es = UnweightedSamples([sessions[session_id].model.observables(x_) for x_ in x])
            pm = {
                    'mean': es.mean,
                    'cov': es.cov.tolist()
                }
        elif mode == 'uncertain_data':
            x = sessions[session_id].state_est.x.sample(100)
            pm = UnweightedSamples([sessions[session_id].model.observables(x_) for x_ in x])
            return pickle.dumps({
                "time": sessions[session_id].state_est.t,
                "performance_metrics": pm})
        else:
            abort(400, f'Invalid return mode: {mode}') 

        return jsonify({
            "time": sessions[session_id].state_est.t,
            "performance_metrics": pm})   

def get_predicted_states(session_id):
    """
    Get the predicted states for the session's model.

    Args:
        session_id: The session ID.

    Returns:
        The predicted states of the session.
    """
    if session_id not in sessions:
        abort(400, f'Session {session_id} does not exist or has ended')
    if not sessions[session_id].initialized:
        abort(400, 'Model not initialized')

    app.logger.debug("Get predicted states for session {}".format(session_id)) 
    mode = request.args.get('return_format', 'mean')
    with sessions[session_id].locks['results']:
        if sessions[session_id].results is None:
            abort(400, 'No Completed Prediction')
        
        states = sessions[session_id].results[1]['states']

        if mode == 'mean':
            states = [{
                'time': states.times[i], 
                'state': states.snapshot(i).mean
             } for i in range(len(states.times))]
        elif mode == 'metrics':
            states = [{
                'time': states.times[i], 
                'state': states.snapshot(i).metrics()
             } for i in range(len(states.times))]
        elif mode == 'multivariate_norm':
            states = [{
                'time': states.times[i], 
                'state': {
                    'mean': states.snapshot(i).mean,
                    'cov': states.snapshot(i).cov.tolist()
                }
             } for i in range(len(states.times))]
        elif mode == 'uncertain_data':
            return pickle.dumps({
                "prediction_time": sessions[session_id].results[1]['time'],
                "states": states})
        else:
            abort(400, f'Invalid return mode: {mode}') 
        
        return jsonify({
            "prediction_time": sessions[session_id].results[1]['time'],
            "states": states})

def get_predicted_event_state(session_id):
    """
    Get the predicted event state for the session's model.

    Args:
        session_id: The session ID.

    Returns:
        The predicted event state of the session.
    """
    if session_id not in sessions:
        abort(400, f'Session {session_id} does not exist or has ended')
    if not sessions[session_id].initialized:
        abort(400, 'Model not initialized')

    app.logger.debug("Get predicted event states for session {}".format(session_id)) 
    mode = request.args.get('return_format', 'mean')
    with sessions[session_id].locks['results']:
        if sessions[session_id].results is None:
            abort(400, 'No Completed Prediction')
        
        es = sessions[session_id].results[1]['event_states']

        if mode == 'mean':
            event_states = [{
                'time': es.times[i], 
                'state': es.snapshot(i).mean
             } for i in range(len(es.times))]
        elif mode == 'metrics':
            event_states = [{
                'time': es.times[i], 
                'state': es.snapshot(i).metrics()
             } for i in range(len(es.times))]
        elif mode == 'multivariate_norm':
            event_states = [{
                'time': es.times[i], 
                'state': {
                    'mean': es.snapshot(i).mean,
                    'cov': es.snapshot(i).cov.tolist()
                }
             } for i in range(len(es.times))]
        elif mode == 'uncertain_data':
            if isinstance(es, UnweightedSamplesPrediction) and isinstance(es[0], LazySimResult):
                # LazySimResult is un-pickleable in prog_models v1.2.2, so we need to convert it to a SimResult
                es2 = [SimResult(event_state.times, event_state.data) for event_state in es]
                es = UnweightedSamplesPrediction(es.times, es2)
            return pickle.dumps({
                'prediction_time': sessions[session_id].results[1]['time'],
                'event_states': es})
        else:
            abort(400, f'Invalid return mode: {mode}')

        return jsonify({
            "prediction_time": sessions[session_id].results[1]['time'],
            "event_states": event_states})

def get_predicted_perf_metrics(session_id):
    """
    Get the predicted performance metrics for the session's model.

    Args:
        session_id: The session ID.

    Returns:
        The predicted performance metrics of the session.
    """
    if session_id not in sessions:
        abort(400, f'Session {session_id} does not exist or has ended')
    if not sessions[session_id].initialized:
        abort(400, 'Model not initialized')

    app.logger.debug("Get predicted performance metrics for session {}".format(session_id)) 
    mode = request.args.get('return_format', 'mean')
    with sessions[session_id].locks['results']:
        if sessions[session_id].results is None:
            abort(400, 'No Completed Prediction')
        
        states = sessions[session_id].results[1]['states']

        if mode == 'mean':
            pm = [{
                'time': states.times[i], 
                'state': sessions[session_id].model.observables(states.snapshot(i).mean)
             } for i in range(len(states.times))]
        elif mode == 'metrics':
            pm = list()
            for i in range(len(states.times)):
                samples = states.snapshot(i).sample(100)
                samples = UnweightedSamples([sessions[session_id].model.observables(x_) for x_ in samples])
                pm.append({
                    'time': states.times[i], 
                    'state': samples.metrics()
                })
        elif mode == 'multivariate_norm':
            pm = list()
            for i in range(len(states.times)):
                samples = states.snapshot(i).sample(100)
                samples = UnweightedSamples([sessions[session_id].model.observables(x_) for x_ in samples])
                pm.append({
                    'time': states.times[i], 
                    'state': {
                        'mean': samples.mean,
                        'cov': samples.cov.tolist()
                    }
                })
        elif mode == 'uncertain_data':
            pm = list()
            for i in range(len(states.times)):
                samples = states.snapshot(i).sample(100)
                samples = UnweightedSamples([sessions[session_id].model.observables(x_) for x_ in samples])
                pm.append(samples)
            
            return pickle.dumps({
                "prediction_time": sessions[session_id].results[1]['time'],
                "performance_metrics": Prediction(states.times, pm)})
        else:
            abort(400, f'Invalid return mode: {mode}')
        
        return jsonify({
            "prediction_time": sessions[session_id].results[1]['time'],
            "performance_metrics": pm})

def get_predicted_toe(session_id):
    """
    Get the predicted Time of Event (ToE) for the session's model.

    Args:
        session_id: The session ID.

    Returns:
        The predicted toe of the session.
    """
    if session_id not in sessions:
        abort(400, f'Session {session_id} does not exist or has ended')
    if not sessions[session_id].initialized:
        abort(400, 'Model not initialized')
    
    mode = request.args.get('return_format', 'metrics')
    app.logger.debug(f"Get prediction for session {session_id} (mode {mode})") 
    with sessions[session_id].locks['results']:
        if sessions[session_id].results is None:
            abort(400, 'No Completed Prediction')
        
        if mode == 'mean':
            toe = sessions[session_id].results[1]['time of event'].mean
        elif mode == 'metrics':
            toe = sessions[session_id].results[1]['time of event'].metrics()
        elif mode == 'multivariate_norm':
            toe = {
                'mean': sessions[session_id].results[1]['time of event'].mean,
                'cov': sessions[session_id].results[1]['time of event'].cov.tolist()
            }
        elif mode == 'uncertain_data':
            return pickle.dumps({
                "prediction_time": sessions[session_id].results[1]['time'],
                'time_of_event': sessions[session_id].results[1]['time of event']})
        else:
            abort(400, f'Invalid return mode: {mode}')

        return jsonify({
            "prediction_time": sessions[session_id].results[1]['time'],
            "time_of_event": toe})
