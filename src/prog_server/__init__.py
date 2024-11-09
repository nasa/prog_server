# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

from .models.prog_server import server
import time

__version__ = '1.7.0'

def run(**kwargs):
    """
    Start the server and block until it is stopped.

    Args:
        host (str, optional): Server host. Defaults to '127.0.0.1'.
        port (int, optional): Server port. Defaults to 8555.
        debug (bool, optional): If the server is started in debug mode
    """
    server.run(**kwargs)

def start(timeout=10, **kwargs):
    """
    Start the server (not blocking).

    Args:
        timeout (float, optional): Timeout in seconds for starting the service

    Keyword Args:
        host (str, optional): Server host. Defaults to '127.0.0.1'.
        port (int, optional): Server port. Defaults to 8555.
        debug (bool, optional): If the server is started in debug mode
    """
    server.start(**kwargs)
    for i in range(timeout):
        if server.is_running():
            return
        time.sleep(1)
    server.stop()
    raise Exception("Server startup timeout")

def stop(timeout=10):
    """
    Stop the server.

    Args:
        timeout (float, optional): Timeout in seconds for starting the service
    """
    server.stop()
    for i in range(timeout):
        if not server.is_running():
            return
        time.sleep(1)
    raise Exception("Server startup timeout")

def is_running():
    """
    Check if the server is running.
    """
    return server.is_running()
