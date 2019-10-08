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
from .util import grid_cmp

from pyhaystack.client import widesky

# hszinc has its own tests, we'll assume they work
import hszinc

# For date/time generation
import datetime
import pytz
import time

# Logging setup so we can see what's going on
import logging

logging.basicConfig(level=logging.DEBUG)

from pyhaystack.client import widesky

BASE_URI = "https://myserver/api/"


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
