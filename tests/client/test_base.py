#!python
# -*- coding: utf-8 -*-
"""
Core Haystack Session client tests.  This class is intended to test the
core functions of PyHaystack's session class.
"""

# Assume unicode literals as per Python 3
from __future__ import unicode_literals

import pytest

from pyhaystack.client.http import dummy as dummy_http
from pyhaystack.client.http.base import HTTPResponse
from ..util import grid_cmp

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

BASE_URI = "https://myserver/api/"

# For testing _on_http_grid_response:
class DummySession(widesky.WideskyHaystackSession):
    def __init__(self, **kwargs):
        self._on_http_grid_response_called = 0
        self._on_http_grid_response_last_args = None
        super(DummySession, self).__init__(**kwargs)

    def _on_http_grid_response(self, response, *args, **kwargs):
        self._log.debug(
            "Received grid response: response=%r args=%r, kwargs=%r",
            response,
            args,
            kwargs,
        )
        self._on_http_grid_response_called += 1
        self._on_http_grid_response_last_args = (response, args, kwargs)


@pytest.fixture
def server_session():
    """
    Initialise a HaystackSession and dummy HTTP server instance.
    """
    server = dummy_http.DummyHttpServer()
    session = DummySession(
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


@pytest.mark.usefixtures("server_session")
class TestSession(object):
    def test_on_http_grid_response(self, server_session):
        (server, session) = server_session

        # Reset our counter
        session._on_http_grid_response_called = 0
        session._on_http_grid_response_last_args = None

        # Fetch a grid
        op = session._get_grid("dummy", callback=lambda *a, **kwa: None)

        # The operation should still be in progress
        assert not op.is_done

        # There shall be one request
        assert server.requests() == 1
        rq = server.next_request()
        # Make a grid to respond with
        expected = hszinc.Grid()

        expected.column["empty"] = {}
        rq.respond(
            status=200,
            headers={b"Content-Type": "text/zinc"},
            content=hszinc.dump(expected, mode=hszinc.MODE_ZINC),
        )

        # Our dummy function should have been called
        assert session._on_http_grid_response_called == 1
        assert isinstance(session._on_http_grid_response_last_args, tuple)
        assert len(session._on_http_grid_response_last_args) == 3

        (response, args, kwargs) = session._on_http_grid_response_last_args
        assert isinstance(response, HTTPResponse)
        assert len(args) == 0
        assert len(kwargs) == 0

    def test_about(self, server_session):
        (server, session) = server_session
        op = session.about()

        # The operation should still be in progress
        assert not op.is_done

        # There shall be one request
        assert server.requests() == 1
        rq = server.next_request()

        # Request shall be a GET
        assert rq.method == "GET", "Expecting GET, got %s" % rq

        # Request shall be for base + 'api/about'
        assert rq.uri == BASE_URI + "api/about"

        # Accept header shall be given
        assert rq.headers[b"Accept"] == "text/zinc"

        # Make a grid to respond with
        expected = hszinc.Grid()

        expected.column["haystackVersion"] = {}
        expected.column["tz"] = {}
        expected.column["serverName"] = {}
        expected.column["serverTime"] = {}
        expected.column["serverBootTime"] = {}
        expected.column["productName"] = {}
        expected.column["productUri"] = {}
        expected.column["productVersion"] = {}
        expected.column["moduleName"] = {}
        expected.column["moduleVersion"] = {}
        expected.append(
            {
                "haystackVersion": "2.0",
                "tz": "UTC",
                "serverName": "pyhaystack dummy server",
                "serverTime": datetime.datetime.now(tz=pytz.UTC),
                "serverBootTime": datetime.datetime.now(tz=pytz.UTC),
                "productName": "pyhaystack dummy server",
                "productVersion": "0.0.1",
                "productUri": hszinc.Uri("http://pyhaystack.readthedocs.io"),
                "moduleName": "tests.client.base",
                "moduleVersion": "0.0.1",
            }
        )

        rq.respond(
            status=200,
            headers={b"Content-Type": "text/zinc"},
            content=hszinc.dump(expected, mode=hszinc.MODE_ZINC),
        )

        # State machine should now be done
        assert op.is_done
        actual = op.result
        grid_cmp(expected, actual)

    def test_ops(self, server_session):
        (server, session) = server_session
        op = session.ops()

        # The operation should still be in progress
        assert not op.is_done

        # There shall be one request
        assert server.requests() == 1
        rq = server.next_request()

        # Request shall be a GET
        assert rq.method == "GET", "Expecting GET, got %s" % rq

        # Request shall be for base + 'api/ops'
        assert rq.uri == BASE_URI + "api/ops"

        # Accept header shall be given
        assert rq.headers[b"Accept"] == "text/zinc"

        # Make a grid to respond with
        expected = hszinc.Grid()

        expected.column["name"] = {}
        expected.column["summary"] = {}
        expected.extend(
            [
                {"name": "about", "summary": "Summary information for server"},
                {"name": "ops", "summary": "Operations supported by this server"},
                {
                    "name": "formats",
                    "summary": "Grid data formats supported by this server",
                },
                {"name": "read", "summary": "Read records by id or filter"},
                {"name": "hisRead", "summary": "Read historical records"},
                {"name": "hisWrite", "summary": "Write historical records"},
                {"name": "nav", "summary": "Navigate a project"},
                {"name": "watchSub", "summary": "Subscribe to change notifications"},
                {
                    "name": "watchUnsub",
                    "summary": "Unsubscribe from change notifications",
                },
                {"name": "watchPoll", "summary": "Poll for changes in watched points"},
                {"name": "pointWrite", "summary": "Write a real-time value to a point"},
                {"name": "invokeAction", "summary": "Invoke an action on an entity"},
            ]
        )

        rq.respond(
            status=200,
            headers={b"Content-Type": "text/zinc"},
            content=hszinc.dump(expected, mode=hszinc.MODE_ZINC),
        )

        # State machine should now be done
        assert op.is_done
        actual = op.result
        grid_cmp(expected, actual)

    def test_formats(self, server_session):
        (server, session) = server_session
        op = session.formats()

        # The operation should still be in progress
        assert not op.is_done

        # There shall be one request
        assert server.requests() == 1
        rq = server.next_request()

        # Request shall be a GET
        assert rq.method == "GET", "Expecting GET, got %s" % rq

        # Request shall be for base + 'api/formats'
        assert rq.uri == BASE_URI + "api/formats"

        # Accept header shall be given
        assert rq.headers[b"Accept"] == "text/zinc"

        # Make a grid to respond with
        expected = hszinc.Grid()

        expected.column["mime"] = {}
        expected.column["receive"] = {}
        expected.column["send"] = {}
        expected.extend(
            [
                {"mime": "text/csv", "receive": hszinc.MARKER, "send": hszinc.MARKER},
                {"mime": "text/zinc", "receive": hszinc.MARKER, "send": hszinc.MARKER},
                {
                    "mime": "application/json",
                    "receive": hszinc.MARKER,
                    "send": hszinc.MARKER,
                },
            ]
        )

        rq.respond(
            status=200,
            headers={b"Content-Type": "text/zinc"},
            content=hszinc.dump(expected, mode=hszinc.MODE_ZINC),
        )

        # State machine should now be done
        assert op.is_done
        actual = op.result
        grid_cmp(expected, actual)

    def test_read_one_id(self, server_session):
        (server, session) = server_session
        op = session.read(hszinc.Ref("my.entity.id"))

        # The operation should still be in progress
        assert not op.is_done

        # There shall be one request
        assert server.requests() == 1
        rq = server.next_request()

        # Request shall be a GET
        assert rq.method == "GET", "Expecting GET, got %s" % rq

        # Request shall be for a specific URI
        assert rq.uri == BASE_URI + "api/read?id=%40my.entity.id"

        # Accept header shall be given
        assert rq.headers[b"Accept"] == "text/zinc"

        # Make a grid to respond with
        expected = hszinc.Grid()

        expected.column["id"] = {}
        expected.column["dis"] = {}
        expected.extend([{"id": hszinc.Ref("my.entity.id"), "dis": "my entity"}])

        rq.respond(
            status=200,
            headers={b"Content-Type": "text/zinc"},
            content=hszinc.dump(expected, mode=hszinc.MODE_ZINC),
        )

        # State machine should now be done
        assert op.is_done
        actual = op.result
        grid_cmp(expected, actual)

    def test_read_many_id(self, server_session):
        (server, session) = server_session
        op = session.read(
            [
                hszinc.Ref("my.entity.id1"),
                hszinc.Ref("my.entity.id2"),
                hszinc.Ref("my.entity.id3"),
            ]
        )

        # The operation should still be in progress
        assert not op.is_done

        # There shall be one request
        assert server.requests() == 1
        rq = server.next_request()

        # Request shall be a GET
        assert rq.method == "POST", "Expecting POST, got %s" % rq

        # Request shall be for a specific URI
        assert rq.uri == BASE_URI + "api/read"

        # Body shall be in ZINC
        assert rq.headers[b"Content-Type"] == "text/zinc"

        # Body shall be a single valid grid of this form:
        expected = hszinc.Grid()
        expected.column["id"] = {}
        expected.extend(
            [
                {"id": hszinc.Ref("my.entity.id1")},
                {"id": hszinc.Ref("my.entity.id2")},
                {"id": hszinc.Ref("my.entity.id3")},
            ]
        )
        actual = hszinc.parse(
            rq.body.decode("utf-8"), mode=hszinc.MODE_ZINC, single=True
        )
        grid_cmp(expected, actual)

        # Accept header shall be given
        assert rq.headers[b"Accept"] == "text/zinc"

        # Make a grid to respond with
        expected = hszinc.Grid()

        expected.column["id"] = {}
        expected.column["dis"] = {}
        expected.extend(
            [
                {"id": hszinc.Ref("my.entity.id1"), "dis": "my entity 1"},
                {"id": hszinc.Ref("my.entity.id2"), "dis": "my entity 2"},
                {"id": hszinc.Ref("my.entity.id3"), "dis": "my entity 3"},
            ]
        )

        rq.respond(
            status=200,
            headers={b"Content-Type": "text/zinc"},
            content=hszinc.dump(expected, mode=hszinc.MODE_ZINC),
        )

        # State machine should now be done
        assert op.is_done
        actual = op.result
        grid_cmp(expected, actual)
