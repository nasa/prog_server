# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

from concurrent.futures import ThreadPoolExecutor as PoolExecutor
from datetime import datetime
from flask import current_app as app
from prog_algs import state_estimators, metrics

pool = PoolExecutor(max_workers=5)

# Prediction Function
def predict(session):
    with session['locks']['execution']:
        with session['locks']['estimate']:
            print(type(session['state_est']))
            if isinstance(session['state_est'], state_estimators.unscented_kalman_filter.UnscentedKalmanFilter):
                samples = session['state_est'].x.sample(20)
            else: # Particle Filter
                samples = session['state_est'].x.raw_samples()
        
        app.logger.debug("  - Starting Prediction Step for session {}".format(session['id']))
        (times, inputs, states, outputs, event_states, events) = session['pred'].predict(samples, session['future loading'], dt=0.1)
    app.logger.debug("  - Finished Prediction Step for session {}".format(session['id']))
    last_event_state = [sample[-1] for sample in event_states]
    final_event_state = {}
    for event_name in session['model'].events:
        final_event_state[event_name] = metrics.eol_metrics(
            [sample[event_name] for sample in last_event_state]
        )

    with session['locks']['results']:
        session['results'] = (
            datetime.now(),
            {
            'time of event': metrics.eol_metrics(events),
            'final event state': final_event_state
        })

def add_to_predict_queue(session):
    with session.locks['futures']:
        if (session.futures[1] is None) or session.futures[1].done():
            # At least one open slot
            app.logger.debug("Performing Prediction for Session {}".format(session['id']))
            session.futures[1] = session.futures[0]
            session.futures[0] = pool.submit(predict, session)
        elif session.futures[0].done():
            # Session 1 finished before 0
            app.logger.debug("Performing Prediction for Session {}".format(session['id']))
            session['futures'][0] = pool.submit(predict, session)
        else:
            app.logger.debug("Prediction skipped for Session {}".format(session['id']))
