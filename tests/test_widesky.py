# -*- coding: utf-8 -*-
"""
Tests for WideSky session object
"""

# Assume unicode literals as per Python 3
from __future__ import unicode_literals

import pytest

from pyhaystack.client.http import dummy as dummy_http
from pyhaystack.client.http.base import HTTPResponse
from pyhaystack.client.http.exceptions import HTTPStatusError
from pyhaystack.util.asyncexc import AsynchronousException

from pyhaystack.client import widesky

# hszinc has its own tests, we'll assume they work
import hszinc

# For date/time generation
import time

# JSON encoding/decoding
import json

# Logging setup so we can see what's going on
import logging

logging.basicConfig(level=logging.DEBUG)

BASE_URI = "https://myserver/api/"


class DummyWsOperation(object):
    result = {
        "token_type": "Bearer",
        "access_token": "abc123",
        "expires_in": (time.time() + 1.0) * 1000.0,
    }


@pytest.fixture
def server_session():
    """
    Initialise a HaystackSession and dummy HTTP server instance.
    """
    server = dummy_http.DummyHttpServer()
    session = widesky.WideskyHaystackSession(
        uri=BASE_URI,
        username="testuser",
        password="testpassword",
        client_id="testclient",
        client_secret="testclientsecret",
        http_client=dummy_http.DummyHttpClient,
        http_args={"server": server, "debug": True},
        grid_format=hszinc.MODE_ZINC,
    )

    # Force an authentication.
    op = session.authenticate()

    # Pop the request off the stack.  We'll assume it's fine for now.
    rq = server.next_request()
    assert server.requests() == 0, "More requests waiting"
    rq.respond(
        status=200,
        headers={b"Content-Type": "application/json"},
        content="""{
                "token_type": "Bearer",
                "access_token": "DummyAccessToken",
                "refresh_token": "DummyRefreshToken",
                "expires_in": %f
            }"""
        % ((time.time() + 86400) * 1000.0),
    )
    assert op.state == "done"
    logging.debug("Result = %s", op.result)
    assert server.requests() == 0
    assert session.is_logged_in
    return (server, session)


class TestImpersonateParam(object):
    """
    Test is_logged_in property
    """

    def test_impersonate_is_set_in_client_header(self):
        """
        is_logged_in == False if _auth_result is None.
        """
        user_id = "12345ab"
        server = dummy_http.DummyHttpServer()
        session = widesky.WideskyHaystackSession(
            uri=BASE_URI,
            username="testuser",
            password="testpassword",
            client_id="testclient",
            client_secret="testclientsecret",
            impersonate=user_id,
            http_client=dummy_http.DummyHttpClient,
            http_args={"server": server, "debug": True},
        )

        session._on_authenticate_done(DummyWsOperation())

        assert session._client.headers["X-IMPERSONATE"] is user_id


@pytest.mark.usefixtures("server_session")
class TestUpdatePassword(object):
    """
    Test the update_password op
    """

    def test_update_pwd_endpoint_is_called(self, server_session):
        (server, session) = server_session

        # Issue the request
        op = session.update_password("hello123X")

        # Make sure there's no error during set-up.
        assert (not op.is_done) or (op.result is None)

        # Pop the request off the stack and inspect it
        rq = server.next_request()
        assert server.requests() == 0, "More requests waiting"

        assert rq.headers.get("Authorization") == b"Bearer DummyAccessToken"
        body = json.loads(rq.body)
        assert body == {"newPassword": "hello123X"}

        rq.respond(
            status=200, headers={b"Content-Type": "application/json"}, content="{}"
        )

        assert op.state == "done"
        logging.debug("Result = %s", op.result)
        assert server.requests() == 0

        op.wait()
        assert op.result is None


class TestIsLoggedIn(object):
    """
    Test is_logged_in property
    """

    def test_returns_false_if_no_auth_result(self):
        """
        is_logged_in == False if _auth_result is None.
        """
        server = dummy_http.DummyHttpServer()
        session = widesky.WideskyHaystackSession(
            uri=BASE_URI,
            username="testuser",
            password="testpassword",
            client_id="testclient",
            client_secret="testclientsecret",
            http_client=dummy_http.DummyHttpClient,
            http_args={"server": server, "debug": True},
        )

        # Straight off the bat, this should be None
        assert session._auth_result is None

        # Therefore, we should see a False result here
        assert not session.is_logged_in

    def test_returns_false_if_no_expires_in(self):
        server = dummy_http.DummyHttpServer()
        session = widesky.WideskyHaystackSession(
            uri=BASE_URI,
            username="testuser",
            password="testpassword",
            client_id="testclient",
            client_secret="testclientsecret",
            http_client=dummy_http.DummyHttpClient,
            http_args={"server": server, "debug": True},
        )

        # Inject our own auth result, empty dict.
        session._auth_result = {}

        # We should see a False result here
        assert not session.is_logged_in

    def test_returns_false_if_expires_in_past(self):
        server = dummy_http.DummyHttpServer()
        session = widesky.WideskyHaystackSession(
            uri=BASE_URI,
            username="testuser",
            password="testpassword",
            client_id="testclient",
            client_secret="testclientsecret",
            http_client=dummy_http.DummyHttpClient,
            http_args={"server": server, "debug": True},
        )

        # Inject our own auth result, expiry in the past.
        session._auth_result = {
            # Milliseconds here!
            "expires_in": (time.time() - 1.0)
            * 1000.0
        }

        # We should see a False result here
        assert not session.is_logged_in

    def test_returns_true_if_expires_in_future(self):
        server = dummy_http.DummyHttpServer()
        session = widesky.WideskyHaystackSession(
            uri=BASE_URI,
            username="testuser",
            password="testpassword",
            client_id="testclient",
            client_secret="testclientsecret",
            http_client=dummy_http.DummyHttpClient,
            http_args={"server": server, "debug": True},
        )

        # Inject our own auth result, expiry in the future.
        session._auth_result = {
            # Milliseconds here!
            "expires_in": (time.time() + 1.0)
            * 1000.0
        }

        # We should see a True result here
        assert session.is_logged_in


class TestOnHTTPGridResponse(object):
    """
    Test _on_http_grid_response
    """

    def test_no_op_if_response_not_401(self):
        """
        Function does nothing if the response is not a 401 response.
        """
        server = dummy_http.DummyHttpServer()
        session = widesky.WideskyHaystackSession(
            uri=BASE_URI,
            username="testuser",
            password="testpassword",
            client_id="testclient",
            client_secret="testclientsecret",
            http_client=dummy_http.DummyHttpClient,
            http_args={"server": server, "debug": True},
        )

        # Seed this with parameters
        auth_result = {
            "expires_in": (time.time() + 3600.0) * 1000.0,
            "access_token": "abcdefgh",
            "refresh_token": "12345678",
        }
        session._auth_result = auth_result

        # A dummy response, we don't care much about the content.
        res = HTTPResponse(status_code=200, headers={}, body="")

        # This should do nothing
        session._on_http_grid_response(res)

        # Same keys
        assert set(auth_result.keys()) == set(
            session._auth_result.keys()
        ), "Keys mismatch"
        for key in auth_result.keys():
            assert auth_result[key] == session._auth_result[key], (
                "Mismatching key %s" % key
            )

    def test_logout_if_response_401(self):
        """
        Function drops the session if the response is a 401 response.
        """
        server = dummy_http.DummyHttpServer()
        session = widesky.WideskyHaystackSession(
            uri=BASE_URI,
            username="testuser",
            password="testpassword",
            client_id="testclient",
            client_secret="testclientsecret",
            http_client=dummy_http.DummyHttpClient,
            http_args={"server": server, "debug": True},
        )

        # Seed this with parameters
        auth_result = {
            "expires_in": (time.time() + 3600.0) * 1000.0,
            "access_token": "abcdefgh",
            "refresh_token": "12345678",
        }
        session._auth_result = auth_result

        # A dummy response, we don't care much about the content.
        res = HTTPResponse(status_code=401, headers={}, body="")

        # This should drop our session
        session._on_http_grid_response(res)
        assert session._auth_result is None

    def test_logout_if_response_401_via_exception(self):
        """
        Function handles HTTPStatusError with code 401 like a 401 response.
        """
        server = dummy_http.DummyHttpServer()
        session = widesky.WideskyHaystackSession(
            uri=BASE_URI,
            username="testuser",
            password="testpassword",
            client_id="testclient",
            client_secret="testclientsecret",
            http_client=dummy_http.DummyHttpClient,
            http_args={"server": server, "debug": True},
        )

        # Seed this with parameters
        auth_result = {
            "expires_in": (time.time() + 3600.0) * 1000.0,
            "access_token": "abcdefgh",
            "refresh_token": "12345678",
        }
        session._auth_result = auth_result

        # Generate a HTTPStatusError, wrap it up in an AsynchronousException
        try:
            raise HTTPStatusError("Unauthorized", 401)
        except HTTPStatusError:
            res = AsynchronousException()

        # This should drop our session
        session._on_http_grid_response(res)
        assert session._auth_result is None

    def test_no_op_if_exception_not_http_status_error(self):
        """
        Function ignores exceptions other than HTTP status errors.
        """
        server = dummy_http.DummyHttpServer()
        session = widesky.WideskyHaystackSession(
            uri=BASE_URI,
            username="testuser",
            password="testpassword",
            client_id="testclient",
            client_secret="testclientsecret",
            http_client=dummy_http.DummyHttpClient,
            http_args={"server": server, "debug": True},
        )

        # Seed this with parameters
        auth_result = {
            "expires_in": (time.time() + 3600.0) * 1000.0,
            "access_token": "abcdefgh",
            "refresh_token": "12345678",
        }
        session._auth_result = auth_result

        # Generate a dummy exception, wrap it up in an AsynchronousException
        class DummyError(Exception):
            pass

        try:
            raise DummyError("Testing")
        except DummyError:
            res = AsynchronousException()

        # This should do nothing
        session._on_http_grid_response(res)

        # Same keys
        assert set(auth_result.keys()) == set(
            session._auth_result.keys()
        ), "Keys mismatch"
        for key in auth_result.keys():
            assert auth_result[key] == session._auth_result[key], (
                "Mismatching key %s" % key
            )
