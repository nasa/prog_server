# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

from ..app import app
from multiprocessing import Process
import requests

class ProgServer():
    """
    This class is a wrapper for the flask server.
    """

    def __init__(self):
        self.process = None

    def run(self, host='127.0.0.1', port=5000, debug=False) -> None:
        """Run the server (blocking)

        Args:
            host (str, optional): Server host. Defaults to '127.0.0.1'.
            port (int, optional): Server port. Defaults to 5000.
        """
        self.process = app.run(host = host, port = port, debug=debug)        

    def start(self, **kwargs) -> None:
        """Start the server in a separate process
        
        Args:
            **kwargs: Arbitrary keyword arguments. See `run` for details.
        """
        if self.process and self.process.is_alive():
            raise RuntimeError('Server already running')
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
            url = "http://127.0.0.1:5000/api/v1/"
            try:
                requests.request("GET", url)
                return True
            except requests.exceptions.ConnectionError:
                return False
        return False

server = ProgServer()
