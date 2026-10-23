# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

import sys

from prog_server.models.prog_server import server

if __name__ == '__main__':
    # Run the server when package is run as a script. (e.g., python -m prog_server)
    debug = '--debug' in sys.argv or '-d' in sys.argv
    server.run(debug = debug)
