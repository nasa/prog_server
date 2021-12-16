# Copyright © 2021 United States Government as represented by the Administrator of the National Aeronautics and Space Administration. All Rights Reserved.

import unittest

if __name__ == '__main__':
    l = unittest.TestLoader()

    was_successful = True

    try:
        pass
    except Exception:
        was_successful = False

    if not was_successful:
        raise Exception('Tests Failed')
