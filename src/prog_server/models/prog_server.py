# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

from copy import deepcopy
from prog_server.app import app
from prog_server.models import session

from multiprocessing import Process
import requests
from progpy import PrognosticsModel

DEFAULT_PORT = 8555
DEFAULT_HOST = '127.0.0.1'


class ProgServer():
    """
    This class is a wrapper for the flask server.
    """

    def __init__(self):
        self.process = None

    def run(self, host=DEFAULT_HOST, port=DEFAULT_PORT, debug=False, models={}, **kwargs) -> None:
        """Run the server (blocking)

        Keyword Args:
            host (str, optional): Server host. Defaults to '127.0.0.1'.
            port (int, optional): Server port. Defaults to 18555.
            debug (bool, optional): If the server is started in debug mode
            models (dict[str, PrognosticsModel]): a dictionary of extra models to consider. The key is the name used to identify it. 
        """
        if not isinstance(models, dict):
            raise TypeError("Extra models (`model` arg in prog_server.run() or start()) must be in a dictionary in the form `name: model_name`")

        session.extra_models.update(models)

        self.host = host
        self.port = port
        self.process = app.run(host=host, port=port, debug=debug)

    def start(self, host=DEFAULT_HOST, port=DEFAULT_PORT, **kwargs) -> None:
        """Start the server in a separate process
        
        Args:
            **kwargs: Arbitrary keyword arguments. See `run` for details.
        """
        if self.process and self.process.is_alive():
            raise RuntimeError('Server already running')
        self.host = host
        self.port = port
        kwargs['host'] = host
        kwargs['port'] = port
                    
        self.process = Process(target=self.run, kwargs=kwargs)
        self.process.start()

    def stop(self) -> None:
        """Stop the server process"""
        self.process.terminate()

    def is_running(self):
        """Check if the server is running"""
        if not self.process:
            return False
        if (isinstance(self.process, Process) and self.process.is_alive()) or not isinstance(self.process, Process):
            url = f"http://{self.host}:{self.port}/api/v1/"
            try:
                requests.request("GET", url)
                return True
            except requests.exceptions.ConnectionError:
                return False
        return False

server = ProgServer()
