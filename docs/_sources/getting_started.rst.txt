Getting Started
===============

The NASA Prognostics As-A-Service (PaaS) Sandbox (a.k.a., `prog_server``) is a simplified implementation of a Software Oriented Architecture (SOA) for performing prognostics (estimation of time until events and future system states) of engineering systems. The PaaS Sandbox is a wrapper around the `Prognostics Algorithms Package <https://github.com/nasa/prog_algs>`__ and `Prognostics Models Package <https://github.com/nasa/prog_models>`__, allowing one or more users to access the features of these packages through a REST API. The package is intended to be used as a research tool to prototype and benchmark Prognostics As-A-Service (PaaS) architectures and work on the challenges facing such architectures, including Generality, Communication, Security, Environmental Complexity, Utility, and Trust.

Installing
-----------------------

Installing from pip (recommended)
********************************************
The latest stable release of `prog_server` is hosted on PyPi. For most users (unless you want to contribute to the development of `prog_server`), the version on PyPi will be adequate. To install from the command line, use the following command:

.. code-block:: console

    $ pip install prog_server

Installing pre-release versions with GitHub
********************************************
For users who would like to contribute to `prog_server` or would like to use pre-release features can do so using the 'dev' branch (or a feature branch) on the `prog_server GitHub repo <https://github.com/nasa/prog_server>`__. This isn't recommended for most users as this version may be unstable. To use this version, use the following commands:

.. code-block:: console

    $ git clone https://github.com/nasa/prog_server
    $ cd prog_server
    $ git checkout dev 
    $ pip install -e .

Summary
---------
A few definitions to get started:

* **events**: something that can be predicted (e.g., system failure). An event has either occurred or not. 

* **event state**: progress towards event occurring. Defined as a number where an event state of 0 indicates the event has occurred and 1 indicates no progress towards the event (i.e., fully healthy operation for a failure event). For gradually occurring events (e.g., discharge) the number will progress from 1 to 0 as the event nears. In prognostics, event state is frequently called "State of Health".

* **inputs**: control applied to the system being modeled (e.g., current drawn from a battery).

* **outputs**: measured sensor values from a system (e.g., voltage and temperature of a battery).

* **performance metrics**: performance characteristics of a system that are a function of system state, but are not directly measured.

* **states**: Internal parameters (typically hidden states) used to represent the state of the system- can be same as inputs/outputs but do not have to be. 

* **process noise**: representing uncertainty in the model transition (e.g., model uncertainty). 

* **measurement noise**: representing uncertainty in the measurement process (e.g., sensor sensitivity, sensor misalignements, environmental effects).

`prog_server` uses the `Prognostics Algorithms Package <https://github.com/nasa/prog_algs>`__ and `Prognostics Models Package <https://github.com/nasa/prog_models>`__. The best way to learn how to use prog_server is to first learn how to use these packages. See `Prognostics Algorithms Package Docs <https://nasa.github.io/prog_algs>`__ and `Prognostics Models Package Docs <https://nasa.github.io/prog_models>`__ for more details.

The PaaS Sandbox is actually two packages, `prog_server` and `prog_client`. The `prog_server` package is the server that provides the REST API. The `prog_client` package is a python client that uses the REST API (see `prog_client <prog_client.html>`__). The `prog_server` package is the PaaS Sandbox Server. Once started the server can accept requests from one or more applications requesting prognostics, using its REST API (described in `prog_server_api`). 

Use 
----
There are two methods for starting the prog_server. The first is by running the module directly. For example,

.. code-block:: console

    $ python -m prog_server

The second method is by starting it programatically in python. For example,

    >>> import prog_server
    >>> prog_server.start() # Starts the server in a new process (is non-blocking)
    >>> ...
    >>> prog_server.stop() # Stops the server

or 

    >>> import prog_server
    >>> prog_server.run() # Starts the server- blocking.

The best way to learn how to use prog_server is to look at examples. There are a number of examples included with prog_server, listed below:

.. |br| raw:: html

     <br>

* :download:`examples.online_prog <../examples/online_prog.py>`
    .. automodule:: examples.online_prog

|br|
    |
* :download:`examples.option_scoring <../examples/option_scoring.py>`
    .. automodule:: examples.option_scoring
    |
