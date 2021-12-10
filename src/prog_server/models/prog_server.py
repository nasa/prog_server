# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

from ..app import app
from multiprocessing import Process

class ProgServer():
    """
    This class is a wrapper for the flask server.
    """

    def run(self, host='127.0.0.1', port=5000) -> None:
        """Run the server (blocking)

        Args:
            host (str, optional): Server host. Defaults to '127.0.0.1'.
            port (int, optional): Server port. Defaults to 5000.
        """
        self.process = app.run(host = host, port = port)
        

    def start(self, **kwargs) -> None:
        """Start the server in a separate process
        
        Args:
            **kwargs: Arbitrary keyword arguments. See `run` for details.
        """
        if self.process.is_alive():
            raise RuntimeError('Server already running')
        self.process = Process(target=self.run, kwargs=kwargs)
        self.process.start()

    def stop(self) -> None:
        """Stop the server process"""
        self.process.terminate()

server = ProgServer()
