# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

"""Client loading updates agree with the actual Flask endpoint."""
from copy import deepcopy
from io import BytesIO
import json
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

import requests

from prog_client import Session
from prog_server import controllers
from prog_server.app import app


def response(status, body=b""):
    result = requests.Response()
    result.status_code = status
    result._content = body
    return result


class LoadingResponseTest(unittest.TestCase):
    def setUp(self):
        with patch("prog_client.session.requests.put", return_value=response(
                201, b'{"session_id": 1}')):
            self.session = Session("ThrownObject", host="example.invalid")

    def test_accepts_current_and_no_content_responses(self):
        config = {"load": {"input": 1.5}}
        original = deepcopy(config)
        for status, body in [(200, b'{"type":"Const","cfg":{}}'), (204, b"")]:
            with self.subTest(status=status), patch(
                    "prog_client.session.requests.post",
                    return_value=response(status, body)) as post:
                self.assertIsNone(self.session.send_loading("Const", config))
                post.assert_called_once_with(
                    self.session.host + "/loading",
                    data={"type": "Const", "cfg": json.dumps(config)})
        self.assertEqual(config, original)

    def test_other_statuses_preserve_error_body(self):
        for status in [201, 202, 302, 400, 404, 500, 503]:
            with self.subTest(status=status), patch(
                    "prog_client.session.requests.post",
                    return_value=response(status, b"loading rejected")) as post:
                with self.assertRaisesRegex(Exception, "^loading rejected$"):
                    self.session.send_loading("Const", {"load": {}})
                self.assertEqual(post.call_count, 1)

    def test_transport_error_propagates_without_retry(self):
        error = requests.ConnectionError("unavailable")
        with patch("prog_client.session.requests.post", side_effect=error) as post:
            with self.assertRaises(requests.ConnectionError) as raised:
                self.session.send_loading("Const", {"load": {}})
            self.assertIs(raised.exception, error)
            self.assertEqual(post.call_count, 1)

    def test_invalid_configuration_is_not_sent(self):
        with patch("prog_client.session.requests.post") as post:
            with self.assertRaises(TypeError):
                self.session.send_loading("Const", {"load": object()})
            post.assert_not_called()


class LoadingEndpointTest(unittest.TestCase):
    def setUp(self):
        self.flask_client = app.test_client()
        self.requests = []
        self.queue = self.start_patch(patch(
            "prog_server.models.session.add_to_predict_queue"))
        self.start_patch(patch.dict(controllers.sessions, {}, clear=True))
        self.start_patch(patch.object(controllers, "session_count", 0))
        self.start_patch(patch("requests.sessions.Session.send", self.send))
        self.client = Session("ThrownObject", host="example.invalid",
                              load_est="Const", load_est_cfg={"load": {}})
        self.queue.reset_mock()

    def start_patch(self, patcher):
        value = patcher.start()
        self.addCleanup(patcher.stop)
        return value

    def send(self, request, **kwargs):
        # Run real HTTP encoding and Flask routing without opening a socket.
        url = urlsplit(request.url)
        self.assertEqual(url.hostname, "example.invalid")
        routed = self.flask_client.open(
            url.path, query_string=url.query, method=request.method,
            data=request.body, headers=dict(request.headers))
        self.requests.append((request, routed.status_code))
        result = response(routed.status_code, routed.data)
        result.headers.update(routed.headers)
        result.url = request.url
        result.request = request
        result.raw = BytesIO(routed.data)
        return result

    def test_constant_loading_update_succeeds(self):
        config = {"load": {"input": 2.5}}
        original = deepcopy(config)
        self.assertIsNone(self.client.send_loading("Const", config))
        self.assertEqual(self.requests[-1][1], 200)
        session = controllers.sessions[self.client.session_id]
        self.assertEqual(session.load_est_name, "Const")
        self.assertEqual(session.load_est(25), config["load"])
        self.queue.assert_called_once_with(session)
        self.assertEqual(config, original)

    def test_piecewise_loading_update_succeeds(self):
        config = {"0": {"input": 1}, "100": {"input": 3}}
        self.assertIsNone(self.client.send_loading("Variable", config))
        session = controllers.sessions[self.client.session_id]
        self.assertEqual(session.load_est(10), {"input": 1})
        self.assertEqual(session.load_est(101), {"input": 3})
        self.queue.assert_called_once_with(session)

    def test_repeated_updates_keep_the_same_session(self):
        for value in [1, 2, 3]:
            self.assertIsNone(self.client.send_loading("Const", {"load": {"u": value}}))
        session = controllers.sessions[self.client.session_id]
        self.assertEqual(session.load_est(0), {"u": 3})
        self.assertEqual(len(controllers.sessions), 1)
        self.assertEqual(self.queue.call_count, 3)

    def test_missing_session_remains_an_error(self):
        controllers.sessions.clear()
        with self.assertRaisesRegex(Exception, "does not exist or has ended"):
            self.client.send_loading("Const", {"load": {}})
        self.assertEqual(self.requests[-1][1], 400)
        self.queue.assert_not_called()

    def test_invalid_estimator_remains_an_error(self):
        with self.assertRaisesRegex(Exception, "not a valid load estimation method"):
            self.client.send_loading("UnknownEstimator", {})
        self.assertEqual(self.requests[-1][1], 400)
        self.queue.assert_not_called()


def run_tests():
    suite = unittest.TestSuite([
        unittest.defaultTestLoader.loadTestsFromTestCase(LoadingResponseTest),
        unittest.defaultTestLoader.loadTestsFromTestCase(LoadingEndpointTest),
    ])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise RuntimeError("Client loading tests failed")


if __name__ == "__main__":
    run_tests()
