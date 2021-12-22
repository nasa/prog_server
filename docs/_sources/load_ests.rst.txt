Load Estimators
################

Load estimators are functions that describe the expected future load. The specific load estimator is specified by class name (e.g., Const) by the load_est key when starting a new session. Each class has specific configuration parameters to be specified in load_est_cfg. By default, MovingAverage is used.

The following load estimators are supported:

.. autofunction:: prog_server.models.load_ests.Const

.. autofunction:: prog_server.models.load_ests.Variable

.. autofunction:: prog_server.models.load_ests.MovingAverage
