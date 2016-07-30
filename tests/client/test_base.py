#!python
# -*- coding: utf-8 -*-
"""
Core Haystack Session client tests.  This class is intended to test the
core functions of PyHaystack's session class.
"""

import pytest

from pyhaystack.client.http import dummy as dummy_http

# For simplicity's sake, we'll just use the WideSky client.
# Pretend we're version 0.0.1.
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

BASE_URI = 'https://myserver/api/'

@pytest.fixture
def server_session():
    """
    Initialise a HaystackSession and dummy HTTP server instance.
    """
    server = dummy_http.DummyHttpServer()
    session = widesky.WideskyHaystackSession(
            uri=BASE_URI,
            username='testuser',
            password='testpassword',
            client_id='testclient',
            client_secret='testclientsecret',
            http_client=dummy_http.DummyHttpClient,
            http_args={'server': server, 'debug': True},
            grid_format=hszinc.MODE_ZINC)
    # Force an authentication.
    op = session.authenticate()
    # Pop the request off the stack.  We'll assume it's fine for now.
    rq = server.next_request()
    assert server.requests() == 0, 'More requests waiting'
    rq.respond(status=200,
            headers={
                'Content-Type': 'application/json'
            },
            content='''{
                "token_type": "Bearer",
                "access_token": "DummyAccessToken",
                "refresh_token": "DummyRefreshToken",
                "expires_in": %f
            }''' % ((time.time() + 86400) * 1000.0))
    assert op.state == 'done'
    logging.debug('Result = %s', op.result)
    assert server.requests() == 0
    assert session.is_logged_in
    return (server, session)


@pytest.mark.usefixtures("server_session")
class TestSession(object):
    def test_about(self, server_session):
        (server, session) = server_session
        op = session.about()

        # There shall be one request
        assert server.requests() == 1
        rq = server.next_request()

        # Request shall be a GET
        assert rq.method == 'GET', 'Expecting GET, got %s' % rq

        # Request shall be for base + 'api/about'
        assert rq.uri == BASE_URI + 'api/about'

        # Accept header shall be given
        assert rq.headers['Accept'] == 'text/zinc'

        # Make a grid to respond with
        res = hszinc.Grid()

        res.column['haystackVersion'] = {}
        res.column['tz'] = {}
        res.column['serverName'] = {}
        res.column['serverTime'] = {}
        res.column['productName'] = {}
        res.column['productUri'] = {}
        res.column['productVersion'] = {}
        res.column['moduleName'] = {}
        res.column['moduleVersion'] = {}
        res.append({
            'haystackVersion': '2.0',
            'tz': 'UTC',
            'serverName': 'pyhaystack dummy server',
            'serverTime': datetime.datetime.now(tz=pytz.UTC),
            'serverBootTime': datetime.datetime.now(tz=pytz.UTC),
            'productName': 'pyhaystack dummy server',
            'productVersion': '0.0.1',
            'moduleName': 'tests.client.base',
            'moduleVersion': '0.0.1',
        })

        rq.respond(status=200, headers={
            'Content-Type': 'text/zinc',
        }, content=hszinc.dump(res, mode=hszinc.MODE_ZINC))
