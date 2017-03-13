# -*- coding: utf-8 -*-
"""
Tests for WideSky session object
"""

# Assume unicode literals as per Python 3
from __future__ import unicode_literals

import pytest

from pyhaystack.client.http import dummy as dummy_http
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

BASE_URI = 'https://myserver/api/'

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
            username='testuser',
            password='testpassword',
            client_id='testclient',
            client_secret='testclientsecret',
            http_client=dummy_http.DummyHttpClient,
            http_args={'server': server, 'debug': True})

        # Straight off the bat, this should be None
        assert session._auth_result is None

        # Therefore, we should see a False result here
        assert not session.is_logged_in

    def test_returns_false_if_no_expires_in(self):
        server = dummy_http.DummyHttpServer()
        session = widesky.WideskyHaystackSession(
            uri=BASE_URI,
            username='testuser',
            password='testpassword',
            client_id='testclient',
            client_secret='testclientsecret',
            http_client=dummy_http.DummyHttpClient,
            http_args={'server': server, 'debug': True})

        # Inject our own auth result, empty dict.
        session._auth_result = {}

        # We should see a False result here
        assert not session.is_logged_in

    def test_returns_false_if_expires_in_past(self):
        server = dummy_http.DummyHttpServer()
        session = widesky.WideskyHaystackSession(
            uri=BASE_URI,
            username='testuser',
            password='testpassword',
            client_id='testclient',
            client_secret='testclientsecret',
            http_client=dummy_http.DummyHttpClient,
            http_args={'server': server, 'debug': True})

        # Inject our own auth result, expiry in the past.
        session._auth_result = {
                # Milliseconds here!
                'expires_in': (time.time() - 1.0) * 1000.0
        }

        # We should see a False result here
        assert not session.is_logged_in

    def test_returns_true_if_expires_in_future(self):
        server = dummy_http.DummyHttpServer()
        session = widesky.WideskyHaystackSession(
            uri=BASE_URI,
            username='testuser',
            password='testpassword',
            client_id='testclient',
            client_secret='testclientsecret',
            http_client=dummy_http.DummyHttpClient,
            http_args={'server': server, 'debug': True})

        # Inject our own auth result, expiry in the future.
        session._auth_result = {
                # Milliseconds here!
                'expires_in': (time.time() + 1.0) * 1000.0
        }

        # We should see a True result here
        assert session.is_logged_in
