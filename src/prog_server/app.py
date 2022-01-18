# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

from .controllers import *
from flask import Flask

app = Flask("prog_server")
app.url_map.strict_slashes = False

PREFIX = '/api/v1'

app.add_url_rule(PREFIX, methods=['GET'], view_func=api_v1)

# Session
app.add_url_rule(PREFIX + '/session', methods=['PUT'], view_func=new_session)
app.add_url_rule(PREFIX + '/session', methods=['GET'], view_func=get_sessions)
app.add_url_rule(PREFIX + '/session/<int:session_id>', methods=['GET'], view_func=get_session)
app.add_url_rule(PREFIX + '/session/<int:session_id>', methods=['DELETE'], view_func=delete_session)

# Set
app.add_url_rule(PREFIX + '/session/<int:session_id>/state', methods=['POST'], view_func=set_state)
app.add_url_rule(PREFIX + '/session/<int:session_id>/loading', methods=['POST'], view_func=set_loading_profile)
app.add_url_rule(PREFIX + '/session/<int:session_id>/data', methods=['POST'], view_func=send_data)

# Get
app.add_url_rule(PREFIX + '/session/<int:session_id>/loading', methods=['GET'], view_func=get_loading_profile)
app.add_url_rule(PREFIX + '/session/<int:session_id>/initialized', methods=['GET'], view_func=get_initialized)
app.add_url_rule(PREFIX + '/session/<int:session_id>/prediction/status', methods=['GET'], view_func=get_prediction_status)

# Get current state
app.add_url_rule(PREFIX + '/session/<int:session_id>/state', methods=['GET'], view_func=get_state)
app.add_url_rule(PREFIX + '/session/<int:session_id>/event_state', methods=['GET'], view_func=get_event_state)
app.add_url_rule(PREFIX + '/session/<int:session_id>/performance_metrics', methods=['GET'], view_func=get_perf_metrics)

# Get Prediction
app.add_url_rule(PREFIX + '/session/<int:session_id>/prediction/state', methods=['GET'], view_func=get_predicted_states)
app.add_url_rule(PREFIX + '/session/<int:session_id>/prediction/event_state', methods=['GET'], view_func=get_predicted_event_state)
app.add_url_rule(PREFIX + '/session/<int:session_id>/prediction/performance_metrics', methods=['GET'], view_func=get_predicted_perf_metrics)
app.add_url_rule(PREFIX + '/session/<int:session_id>/prediction/events', methods=['GET'], view_func=get_predicted_toe)
