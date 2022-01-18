# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

from concurrent.futures import ThreadPoolExecutor as PoolExecutor
from datetime import datetime
from flask import current_app as app
from copy import deepcopy

pool = PoolExecutor(max_workers=5)

# Prediction Function
def predict(session):
    with session.locks['execution']:
        with session.locks['estimate']:
            x = deepcopy(session.state_est.x)
            time = session.state_est.t
        
        (_, _, states, _, event_states, events) = session.pred.predict(x, session.load_est, dt=0.1, t0 = time)

    with session.locks['results']:
        session.results = (
            datetime.now(),
            {
            'time': time,
            'time of event': events,
            'states': states,
            'event_states': event_states
        })

def add_to_predict_queue(session):
    with session.locks['futures']:
        if (session.futures[1] is None) or session.futures[1].done():
            # At least one open slot
            app.logger.debug(f"Performing Prediction for Session {session.session_id}")
            session.futures[1] = session.futures[0]
            session.futures[0] = pool.submit(predict, session)
        elif session.futures[0].done():
            # Session 1 finished before 0
            app.logger.debug(f"Performing Prediction for Session {session.session_id}")
            session.futures[0] = pool.submit(predict, session)
        else:
            app.logger.debug(f"Prediction skipped for Session {session.session_id}")
