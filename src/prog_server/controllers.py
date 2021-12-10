# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

from .models.session import Session
from .models.load_ests import update_moving_avg
from flask import request, abort, jsonify
from flask import current_app as app

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

    if 'model_name' not in request.form:
        abort(400, 'model_name must be specified in request body')

    model_name = request.form['model_name'] # Replace with actual type name

    session_id = session_count
    session_count += 1
    sessions[session_id] = Session(session_id, model_name)
    
    return jsonify(sessions[session_id].to_dict())

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

def set_loading_profile(self, session_id):
    """
    Set the loading profile for the session's model.

    Args:
        session_id: The session ID.
        profile: The new loading profile.
    """
    if session_id not in sessions:
        abort(400, f'Session {session_id} does not exist or has ended')

    app.logger.debug(f"Setting loading profile for Session {session_id}")
    #sessions[session_id].set_load_estimator(request.values['load_est_name'], request.values['load_est_cfg'])
    pass

def send_data(self, session_id):
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
    update_moving_avg(inputs, session_id)

    session.add_data(time, inputs, outputs)

    return '' 

# Get
def get_loading_profile(self, session_id):
    """
    Get the loading profile for the session's model.

    Args:
        session_id: The session ID.

    Returns:
        The loading profile of the session.
    """
    if session_id not in sessions:
        abort(400, f'Session {session_id} does not exist or has ended')

    return jsonify({'name': sessions[session_id].load_estimator.name, 'config': sessions[session_id].load_estimator_cfg})

def get_initialized(self, session_id):
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

def get_prediction_status(self, session_id):
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
        for future in sessions[session_id].future:
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
    return status  

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

    app.logger.debug(f"Getting state for Session {session_id}")
    return sessions[session_id].state_est.x.mean

def get_event_state(self, session_id):
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

    app.logger.debug(f"Getting event state for Session {session_id}")
    x = sessions[session_id].state_est.x.mean
    return sessions[session_id].model.event_state(x)

def get_observables(self, session_id):
    """
    Get the observables for the session's model.

    Args:
        session_id: The session ID.

    Returns:
        The observables of the session.
    """
    if session_id not in sessions:
        abort(400, f'Session {session_id} does not exist or has ended')
    if not sessions[session_id].initialized:
        abort(400, 'Model not initialized')

    app.logger.debug(f"Getting observables for Session {session_id}")
    x = sessions[session_id].state_est.x.mean
    return sessions[session_id].model.observables(x)

def get_predicted_states(self, session_id):
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

    pass

def get_predicted_event_state(self, session_id):
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

    pass

def get_predicted_observables(self, session_id):
    """
    Get the predicted observables for the session's model.

    Args:
        session_id: The session ID.

    Returns:
        The predicted observables of the session.
    """
    if session_id not in sessions:
        abort(400, f'Session {session_id} does not exist or has ended')
    if not sessions[session_id].initialized:
        abort(400, 'Model not initialized')

    pass

def get_predicted_toe(self, session_id):
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

    pass
