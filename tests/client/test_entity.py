#!python
# -*- coding: utf-8 -*-
"""
Haystack Session Entity interface tests.  This class is intended to test the
functions of the high-level entity interface.
"""

# Assume unicode literals as per Python 3
from __future__ import unicode_literals

import pytest

from pyhaystack.client.http import dummy as dummy_http
from pyhaystack.client.entity.entity import Entity

# For simplicity's sake, we'll just use the WideSky client.
# Pretend we're version 0.0.1.
from pyhaystack.client import widesky

# hszinc has its own tests, we'll assume they work
import hszinc

# For date/time generation
import time

# Logging setup so we can see what's going on
import logging

logging.basicConfig(level=logging.DEBUG)

BASE_URI = "https://myserver/api/"


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


@pytest.mark.usefixtures("server_session")
class TestSession(object):
    def test_get_single_entity(self, server_session):
        (server, session) = server_session
        # Try retrieving an existing single entity
        op = session.get_entity("my.entity.id", single=True)

        # The operation should still be in progress
        assert not op.is_done

        # There shall be one request
        assert server.requests() == 1
        rq = server.next_request()

        # Request shall be a GET
        assert rq.method == "GET", "Expecting GET, got %s" % rq

        # Request shall be for base + 'api/read?id=@my.entity.id'
        assert rq.uri == BASE_URI + "api/read?id=%40my.entity.id"

        # Accept header shall be given
        assert rq.headers[b"Accept"] == "text/zinc"

        # Make a grid to respond with
        response = hszinc.Grid()

        response.column["id"] = {}
        response.column["dis"] = {}
        response.column["randomTag"] = {}
        response.append(
            {
                "id": hszinc.Ref("my.entity.id", value="id"),
                "dis": "A test entity",
                "randomTag": hszinc.MARKER,
            }
        )

        rq.respond(
            status=200,
            headers={b"Content-Type": "text/zinc"},
            content=hszinc.dump(response, mode=hszinc.MODE_ZINC),
        )

        # State machine should now be done
        assert op.is_done
        entity = op.result
        # Response should be an entity
        assert isinstance(entity, Entity), "%r not an entity" % entity
        # The tags should be passed through from the response
        assert entity.id.name == "my.entity.id"
        assert entity.tags["dis"] == response[0]["dis"]
        assert entity.tags["randomTag"] == response[0]["randomTag"]

    def test_get_single_entity_missing(self, server_session):
        (server, session) = server_session
        # Try retrieving an existing single entity that does not exist
        op = session.get_entity("my.nonexistent.id", single=True)

        # The operation should still be in progress
        assert not op.is_done

        # There shall be one request
        assert server.requests() == 1
        rq = server.next_request()

        # Request shall be a GET
        assert rq.method == "GET", "Expecting GET, got %s" % rq

        # Request shall be for base + 'api/read?id=@my.nonexistent.id'
        assert rq.uri == BASE_URI + "api/read?id=%40my.nonexistent.id"

        # Accept header shall be given
        assert rq.headers[b"Accept"] == "text/zinc"

        # Make a grid to respond with.  Note, server might also choose to
        # throw an error, but we'll pretend it doesn't.
        response = hszinc.Grid()

        response.column["id"] = {}
        response.column["dis"] = {}

        rq.respond(
            status=200,
            headers={b"Content-Type": "text/zinc"},
            content=hszinc.dump(response, mode=hszinc.MODE_ZINC),
        )

        # State machine should now be done
        assert op.is_done
        # This should trigger a name error:
        try:
            entity = op.result
            assert entity is None
        except NameError as e:
            assert str(e) == "No matching entity found"

    def test_get_multi_entity_missng(self, server_session):
        (server, session) = server_session
        # Try retrieving existing multiple entities, with one that doesn't exist
        op = session.get_entity(
            ["my.entity.id1", "my.entity.id2", "my.nonexistent.id"], single=False
        )

        # The operation should still be in progress
        assert not op.is_done

        # There shall be one request
        assert server.requests() == 1
        rq = server.next_request()

        # Request shall be a POST
        assert rq.method == "POST", "Expecting POST, got %s" % rq

        # Request shall be for base + 'api/read?id=@my.entity.id'
        assert rq.uri == BASE_URI + "api/read"

        # Accept header shall be given
        assert rq.headers[b"Accept"] == "text/zinc"
        assert rq.headers[b"Content-Type"] == "text/zinc"

        # Body shall be a single grid:
        rq_grid = hszinc.parse(
            rq.body.decode("utf-8"), mode=hszinc.MODE_ZINC, single=True
        )

        # It shall have one column; id
        assert set(rq_grid.column.keys()) == set(["id"])
        # It shall have 3 rows
        assert len(rq_grid) == 3
        # Each row should only have 'id' values
        assert all([(set(r.keys()) == set(["id"])) for r in rq_grid])
        # The rows' 'id' column should *only* contain Refs.
        assert all([isinstance(r["id"], hszinc.Ref) for r in rq_grid])
        # Both IDs shall be listed, we don't about order
        assert set([r["id"].name for r in rq_grid]) == set(
            ["my.entity.id1", "my.entity.id2", "my.nonexistent.id"]
        )

        # Make a grid to respond with
        response = hszinc.Grid()

        response.column["id"] = {}
        response.column["dis"] = {}
        response.column["randomTag"] = {}
        response.extend(
            [
                {
                    "id": hszinc.Ref("my.entity.id2", value="id2"),
                    "dis": "A test entity #2",
                    "randomTag": hszinc.MARKER,
                },
                {"id": None, "dis": None, "randomTag": None},
                {
                    "id": hszinc.Ref("my.entity.id1", value="id1"),
                    "dis": "A test entity #1",
                    "randomTag": hszinc.MARKER,
                },
            ]
        )

        rq.respond(
            status=200,
            headers={b"Content-Type": "text/zinc"},
            content=hszinc.dump(response, mode=hszinc.MODE_ZINC),
        )

        # State machine should now be done
        assert op.is_done
        entities = op.result

        # Response should be a dict
        assert isinstance(entities, dict), "%r not a dict" % entities
        # Response should have these keys
        assert set(entities.keys()) == set(["my.entity.id1", "my.entity.id2"])

        entity = entities.pop("my.entity.id1")
        assert isinstance(entity, Entity), "%r not an entity" % entity
        # The tags should be passed through from the response
        assert entity.id.name == "my.entity.id1"
        assert entity.tags["dis"] == response[2]["dis"]
        assert entity.tags["randomTag"] == response[2]["randomTag"]

        entity = entities.pop("my.entity.id2")
        assert isinstance(entity, Entity), "%r not an entity" % entity
        # The tags should be passed through from the response
        assert entity.id.name == "my.entity.id2"
        assert entity.tags["dis"] == response[0]["dis"]
        assert entity.tags["randomTag"] == response[0]["randomTag"]

    def test_get_multi_entity(self, server_session):
        (server, session) = server_session
        # Try retrieving existing multiple entities
        op = session.get_entity(["my.entity.id1", "my.entity.id2"], single=False)

        # The operation should still be in progress
        assert not op.is_done

        # There shall be one request
        assert server.requests() == 1
        rq = server.next_request()

        # Request shall be a POST
        assert rq.method == "POST", "Expecting POST, got %s" % rq

        # Request shall be for base + 'api/read?id=@my.entity.id'
        assert rq.uri == BASE_URI + "api/read"

        # Accept header shall be given
        assert rq.headers[b"Accept"] == "text/zinc"
        assert rq.headers[b"Content-Type"] == "text/zinc"

        # Body shall be a single grid:
        rq_grid = hszinc.parse(
            rq.body.decode("utf-8"), mode=hszinc.MODE_ZINC, single=True
        )

        # It shall have one column; id
        assert set(rq_grid.column.keys()) == set(["id"])
        # It shall have 2 rows
        assert len(rq_grid) == 2
        # Each row should only have 'id' values
        assert all([(set(r.keys()) == set(["id"])) for r in rq_grid])
        # The rows' 'id' column should *only* contain Refs.
        assert all([isinstance(r["id"], hszinc.Ref) for r in rq_grid])
        # Both IDs shall be listed, we don't about order
        assert set([r["id"].name for r in rq_grid]) == set(
            ["my.entity.id1", "my.entity.id2"]
        )

        # Make a grid to respond with
        response = hszinc.Grid()

        response.column["id"] = {}
        response.column["dis"] = {}
        response.column["randomTag"] = {}
        response.extend(
            [
                {
                    "id": hszinc.Ref("my.entity.id1", value="id1"),
                    "dis": "A test entity #1",
                    "randomTag": hszinc.MARKER,
                },
                {
                    "id": hszinc.Ref("my.entity.id2", value="id2"),
                    "dis": "A test entity #2",
                    "randomTag": hszinc.MARKER,
                },
            ]
        )

        rq.respond(
            status=200,
            headers={b"Content-Type": "text/zinc"},
            content=hszinc.dump(response, mode=hszinc.MODE_ZINC),
        )

        # State machine should now be done
        assert op.is_done
        entities = op.result

        # Response should be a dict
        assert isinstance(entities, dict), "%r not a dict" % entities
        # Response should have these keys
        assert set(entities.keys()) == set(["my.entity.id1", "my.entity.id2"])

        entity = entities.pop("my.entity.id1")
        assert isinstance(entity, Entity), "%r not an entity" % entity
        # The tags should be passed through from the response
        assert entity.id.name == "my.entity.id1"
        assert entity.tags["dis"] == response[0]["dis"]
        assert entity.tags["randomTag"] == response[0]["randomTag"]

        entity = entities.pop("my.entity.id2")
        assert isinstance(entity, Entity), "%r not an entity" % entity
        # The tags should be passed through from the response
        assert entity.id.name == "my.entity.id2"
        assert entity.tags["dis"] == response[1]["dis"]
        assert entity.tags["randomTag"] == response[1]["randomTag"]
