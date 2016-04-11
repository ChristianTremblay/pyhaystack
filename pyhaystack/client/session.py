#!python
# -*- coding: utf-8 -*-
"""
Core Haystack Session client object interface.  This file defines an abstract
interface for Project Haystack clients and is responsible for opening and
maintaining a session with the server.
"""

import logging
import hszinc
import weakref
from six import string_types

from .http import sync, exceptions
from .ops import grid

class HaystackSession(object):
    """
    The Haystack Session handler is responsible for presenting an API for
    querying and controlling a Project Haystack server.

    HaystackSession itself is the base class, which is then implemented by way
    of HaystackOperation subclasses which are instantiated by the session
    object before being started and returned.

    These operations by default are specified by class member references
    to the classes concerned.

    Methods for Haystack operations return an 'Operation' object, which
    may be used in any of two ways:
    - as a synchronous result placeholder by calling its `wait` method followed
      by inspection of its `result` attribute.
    - as an asynchronous call manager by connecting a "slot" (`callable` that
      takes keyword arguments) to the `done_sig` signal.

    The base class takes some arguments that control the default behaviour of
    the object.
    """

    def __init__(self, uri, grid_format=hszinc.MODE_ZINC,
                http_client=sync.SyncHttpClient, http_args=None, log=None):
        """
        Initialise a base Project Haystack session handler.

        :param uri: Base URI for the Haystack installation.
        :param grid_format: What format to use for grids in GET/POST requests?
        :param http_client: HTTP client class to use.
        :param http_args: Optional HTTP client arguments to configure.
        :param log: Logging object for reporting messages.
        """
        if log is None:
            log = logging.getLogger('pyhaystack.client.%s' \
                    % self.__class__.__name__)
        self._log = log

        if http_args is None:
            http_args = {}

        if grid_format not in (hszinc.MODE_ZINC, hszinc.MODE_JSON):
            raise ValueError('Unrecognised grid format %s' % grid_format)
        self._grid_format = grid_format

        # Create the HTTP client object
        self._client = http_client(url=url, **http_args)

        # Current in-progress authentication operation, if any.
        self._auth_op = None

    # Public methods/properties

    def authenticate(self, callback=None):
        """
        Authenticate with the Project Haystack server.  If an authentication
        attempt is in progress, we return it, otherwise we instantiate a new
        one.
        """
        if self._auth_op is not None:
            auth_op = self._auth_op()
        else:
            auth_op = None

        new = auth_op is None
        if new:
            auth_op = self._AUTH_OPERATION(self)
            auth_op.done_sig.connect(self._on_authenticate_done)

        if callback is not None:
            if auth_op.is_done:
                # Already done
                return callback(auth_op)
            else:
                auth_op.done_sig.connect(callback)

        if new:
            auth_op.go()
            self._auth_op = weakref.ref(auth_op)

        return auth_op

    def about(self, callback=None):
        """
        Retrieve the version information of this Project Haystack server.
        """
        op = self._ABOUT_OPERATION(self)
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    def ops(self, callback=None):
        """
        Retrieve the operations supported by this Project Haystack server.
        """
        op = self._OPS_OPERATION(self)
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    def formats(sel, callback=None):
        """
        Retrieve the grid formats supported by this Project Haystack server.
        """
        op = self._FORMATS_OPERATION(self)
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    def read(self, ids=None, filter_expr=None, limit=None, callback=None):
        """
        Retrieve information on entities matching the given criteria.
        Either ids or filter_expr may be given.  ids may be given as a
        list or as a single ID string/reference.

        filter_expr is given as a string.  pyhaystack.util.filterbuilder
        may be useful for generating these programatically.

        :param id: ID of a single entity to retrieve
        :param ids: IDs of many entities to retrieve as a list
        :param filter_expr: A filter expression that describes the entities
                            of interest.
        :param limit: A limit on the number of entities to return.
        """
        if isinstance(ids, string_types) or isinstance(ids, hszinc.Ref):
            # Make sure we always pass a list.
            ids = [ids]
        op = self._READ_OPERATION(self, ids, filter_expr, limit)
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    def nav(self, nav_id=None, callback=None):
        """
        The nav op is used navigate a project for learning and discovery. This
        operation allows servers to expose the database in a human-friendly
        tree (or graph) that can be explored.
        """
        op = self._NAV_OPERATION(self, nav_id)
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    def watch_sub(self, points, watch_id=None, watch_dis=None,
            lease=None, callback=None):
        """
        This creates a new watch with debug string watch_dis, identifier
        watch_id (string) and a lease time of lease (integer) seconds.  points
        is a list of strings, Entity objects or hszinc.Ref objects.
        """
        op = self._WATCH_SUB_OPERATION(self, watch_id, watch_dis, lease)
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    def watch_unsub(self, watch, points=None, callback=None):
        """
        watch is either the value of watch_id given when creating a watch, or
        an instance of a Watch object.

        If points is not None, it is a list of strings, Entity objects or
        hszinc.Ref objects which will be removed from the Watch object.
        Otherwise, it closes the Watch object.
        """
        op = self._WATCH_SUB_OPERATION(self, watch, points)
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    def watch_poll(self, watch, refresh=False, callback=None):
        """
        watch is either the value of watch_id given when creating a watch, or
        an instance of a Watch object.

        If refresh is True, then all points on the watch will be updated, not
        just those that have changed since the last poll.
        """
        op = self._WATCH_POLL_OPERATION(self, watch, refresh)
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    def point_write(self, point, level=None, val=None, who=None,
            duration=None, callback=None):
        """
        point is either the ID of the writeable point entity, or an instance of
        the writeable point entity to retrieve the write status of or write a
        value to.

        If level is None, the other parameters are required to be None too, the
        write status of the point is retrieved.  Otherwise, a write is
        performed to the nominated point.
        """
        op = self._POINT_WRITE_OPERATION(self, point, level, val, who, duration)
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    def his_write(self, point, timestamp_records, callback=None):
        """
        point is either the ID of the writeable historical point entity, or an
        instance of the writeable historical point entity to write historical
        data to.  timestamp_records should be a dict mapping timestamps
        (datetime.datetime) to the values to be written at those times, or a
        Pandas Series object.
        """
        op = self._HIS_WRITE_OPERATION(self, point, timestamp_records)
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    def his_read(self, point, rng, callback=None):
        """
        point is either the ID of the historical point entity, or an instance
        of the historical point entity to read historical from.  rng is
        either a string describing a time range (e.g. "today", "yesterday"), a
        datetime.date object (providing all samples on the nominated day), a
        datetime.datetime (providing all samples since the nominated time) or a
        slice of datetime.dates or datetime.datetimes.
        """
        op = self._HIS_READ_OPERATION(self, point, rng)
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    def invoke_action(self, entity, action, **kwargs):
        """
        entity is either the ID of the entity, or an instance of the entity to
        invoke the named action on.  Keyword arguments give any additional
        parameters required for the user action.
        """
        op = self._INVOKE_ACTION_OPERATION(self, entity, action, kwargs)
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    # Protected methods/properties

    def _get(self, uri, callback, **kwargs):
        """
        Perform a raw HTTP GET operation.  This is a convenience wrapper around
        the HTTP client class that allows pre/post processing of the request by
        the session instance.
        """
        return self._client._get(uri, callback, **kwargs)

    def _get_grid(self, uri, callback, expect_format=None, **kwargs):
        """
        Perform a HTTP GET of a grid.
        """
        if expect_format is None:
            expect_format=self._grid_format
        op = self._GET_GRID_OPERATION(self, uri,
                expect_format=expect_format, **kwargs)
        op.done_sig.connect(callback)
        op.go()
        return op

    def _post(self, url, callback, body, body_type=None, body_size=None,
            headers=None, **kwargs):
        """
        Perform a raw HTTP POST operation.  This is a convenience wrapper around
        the HTTP client class that allows pre/post processing of the request by
        the session instance.
        """
        return self._client._post(self, url, callback, body, body_type,
                body_size, headers, **kwargs)

    def _post_grid(self, uri, grid, callback, post_format=None,
            expect_format=None, **kwargs):
        """
        Perform a HTTP POST of a grid.
        """
        if expect_format is None:
            expect_format=self._grid_format
        if post_format is None:
            post_format=self._grid_format
        op = self._POST_GRID_OPERATION(self, uri, expect_format=expect_format,
                post_format=post_format, **kwargs)
        op.done_sig.connect(callback)
        op.go()
        return op

    # Private methods/properties

    def _on_authenticate_done(self, operation, **kwargs):
        """
        Process the result of an authentication operation.  This needs to be
        implemented in the subclass and should, at minimum, set a flag in the
        subclass to indicate the authentication state and clear the _auth_op
        attribute on the base class.
        """
        raise NotImplementedError('To be implemented in %s' % \
                self.__class__.__name__)
