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
from threading import Lock
from six import string_types

from .http import sync
from .ops import grid as grid_ops
from .ops import entity as entity_ops
from .ops import his as his_ops
from .ops import feature as feature_ops
from .entity.models.haystack import HaystackTaggingModel


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

    - as a synchronous result placeholder by calling its `wait` method
    followed by inspection of its `result` attribute.
    - as an asynchronous call manager by connecting a "slot" (`callable`
    that takes keyword arguments) to the `done_sig` signal.

    The base class takes some arguments that control the default behaviour of
    the object.
    """

    # Operation references
    _GET_GRID_OPERATION = grid_ops.GetGridOperation
    _POST_GRID_OPERATION = grid_ops.PostGridOperation
    _GET_ENTITY_OPERATION = entity_ops.GetEntityOperation
    _FIND_ENTITY_OPERATION = entity_ops.FindEntityOperation

    _HIS_READ_SERIES_OPERATION = his_ops.HisReadSeriesOperation
    _HIS_READ_FRAME_OPERATION = his_ops.HisReadFrameOperation
    _HIS_WRITE_SERIES_OPERATION = his_ops.HisWriteSeriesOperation
    _HIS_WRITE_FRAME_OPERATION = his_ops.HisWriteFrameOperation

    _HAS_FEATURES_OPERATION = feature_ops.HasFeaturesOperation

    def __init__(
        self,
        uri,
        api_dir,
        grid_format=hszinc.MODE_ZINC,
        http_client=sync.SyncHttpClient,
        http_args=None,
        tagging_model=HaystackTaggingModel,
        log=None,
        pint=False,
        cache_expiry=3600.0,
    ):
        """
        Initialise a base Project Haystack session handler.

        :param uri: Base URI for the Haystack installation.
        :param api_dir: Subdirectory relative to URI where API calls are made.
        :param grid_format: What format to use for grids in GET/POST requests?
        :param http_client: HTTP client class to use.
        :param http_args: Optional HTTP client arguments to configure.
        :param tagging_model: Entity Tagging model in use.
        :param log: Logging object for reporting messages.
        :param pint: Configure hszinc to use basic quantity or Pint Quanity
        :param cache_expiry: Number of seconds before cached data expires.

        See : https://pint.readthedocs.io/ for details about pint
        """
        if log is None:
            log = logging.getLogger("pyhaystack.client.%s" % self.__class__.__name__)
        self._log = log

        if http_args is None:
            http_args = {}

        # Configure hszinc to use pint or not for Quantity definition
        self.config_pint(pint)

        if grid_format not in (hszinc.MODE_ZINC, hszinc.MODE_JSON):
            raise ValueError("Unrecognised grid format %s" % grid_format)
        self._grid_format = grid_format

        # Create the HTTP client object
        if bool(http_args.pop("debug", None)) and ("log" not in http_args):
            http_args["log"] = log.getChild("http_client")
        self._client = http_client(uri=uri, **http_args)
        self._api_dir = api_dir

        # Current in-progress authentication operation, if any.
        self._auth_op = None

        # Entity references, stored as weakrefs
        self._entities = weakref.WeakValueDictionary()

        # Tagging model in use
        self._tagging_model = tagging_model(self)

        # Grid cache
        self._grid_lk = Lock()
        self._grid_expiry = cache_expiry
        self._grid_cache = {}  # 'op' -> (op, expiry, grid)

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

    def about(self, cache=True, callback=None):
        """
        Retrieve the version information of this Project Haystack server.
        """
        return self._on_about(cache=cache, callback=callback)

    def ops(self, cache=True, callback=None):
        """
        Retrieve the operations supported by this Project Haystack server.
        """
        return self._on_ops(cache=cache, callback=callback)

    def formats(self, cache=True, callback=None):
        """
        Retrieve the grid formats supported by this Project Haystack server.
        """
        return self._on_formats(cache=cache, callback=callback)

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
        return self._on_read(
            ids=ids, filter_expr=filter_expr, limit=limit, callback=callback
        )

    def nav(self, nav_id=None, callback=None):
        """
        The nav op is used navigate a project for learning and discovery. This
        operation allows servers to expose the database in a human-friendly
        tree (or graph) that can be explored.
        """
        return self._on_nav(nav_id=nav_id, callback=callback)

    def watch_sub(
        self, points, watch_id=None, watch_dis=None, lease=None, callback=None
    ):
        """
        This creates a new watch with debug string watch_dis, identifier
        watch_id (string) and a lease time of lease (integer) seconds.  points
        is a list of strings, Entity objects or hszinc.Ref objects.
        """
        return self._on_watch_sub(
            points=points,
            watch_id=watch_id,
            watch_dis=watch_dis,
            lease=lease,
            callback=callback,
        )

    def watch_unsub(self, watch, points=None, callback=None):
        """
        watch is either the value of watch_id given when creating a watch, or
        an instance of a Watch object.

        If points is not None, it is a list of strings, Entity objects or
        hszinc.Ref objects which will be removed from the Watch object.
        Otherwise, it closes the Watch object.
        """
        return self._on_watch_unsub(watch=watch, points=points, callback=callback)

    def watch_poll(self, watch, refresh=False, callback=None):
        """
        watch is either the value of watch_id given when creating a watch, or
        an instance of a Watch object.

        If refresh is True, then all points on the watch will be updated, not
        just those that have changed since the last poll.
        """
        return self._on_watch_poll(watch=watch, refresh=refresh, callback=callback)

    def point_write(
        self, point, level=None, val=None, who=None, duration=None, callback=None
    ):
        """
        point is either the ID of the writeable point entity, or an instance of
        the writeable point entity to retrieve the write status of or write a
        value to.

        If level is None, the other parameters are required to be None too, the
        write status of the point is retrieved.  Otherwise, a write is
        performed to the nominated point.
        """
        who = who or self._username
        return self._on_point_write(
            point=point,
            level=level,
            val=val,
            who=who,
            duration=duration,
            callback=callback,
        )

    def his_read(self, point, rng, callback=None):
        """
        point is either the ID of the historical point entity, or an instance
        of the historical point entity to read historical from.  rng is
        either a string describing a time range (e.g. "today", "yesterday"), a
        datetime.date object (providing all samples on the nominated day), a
        datetime.datetime (providing all samples since the nominated time) or a
        slice of datetime.dates or datetime.datetimes.
        """
        return self._on_his_read(point=point, rng=rng, callback=callback)

    def his_write(self, point, timestamp_records, callback=None):
        """
        point is either the ID of the writeable historical point entity, or an
        instance of the writeable historical point entity to write historical
        data to.  timestamp_records should be a dict mapping timestamps
        (datetime.datetime) to the values to be written at those times, or a
        Pandas Series object.
        """
        return self._on_his_write(
            point=point, timestamp_records=timestamp_records, callback=callback
        )

    def invoke_action(self, entity, action, callback=None, **kwargs):
        """
        entity is either the ID of the entity, or an instance of the entity to
        invoke the named action on.  Keyword arguments give any additional
        parameters required for the user action.
        """
        return self._on_invoke_action(
            entity=entity, action=action, callback=callback, action_args=kwargs
        )

    def get_entity(self, ids, refresh=False, single=None, callback=None):
        """
        Retrieve instances of entities, possibly refreshing them.

        :param ids: A single entity ID, or a list of entity IDs.
        :param refresh: Do we refresh the tags on those entities?
        :param single: Are we expecting a single entity?  Defaults to
                       True if `ids` is not a list.
        :param callback: Asynchronous result callback.
        """
        if isinstance(ids, string_types) or isinstance(ids, hszinc.Ref):
            # Make sure we always pass a list.
            ids = [ids]
            if single is None:
                single = True
        elif single is None:
            single = False

        op = self._GET_ENTITY_OPERATION(self, ids, refresh, single)
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    def find_entity(self, filter_expr, limit=None, single=False, callback=None):
        """
        Retrieve instances of entities that match a filter expression.

        :param filter_expr: The filter expression to search for.
        :param limit: Optional limit to number of entities retrieved.
        :param single: Are we expecting a single entity?  Defaults to
                       True if `ids` is not a list.
        :param callback: Asynchronous result callback.
        """
        op = self._FIND_ENTITY_OPERATION(self, filter_expr, limit, single)
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    def his_read_series(self, point, rng, tz=None, series_format=None, callback=None):
        """
        Read the historical data of the given point and return it as a series.

        :param point: Haystack 'point' entity to read the data from
        :param rng: Historical read range for the 'point'
        :param tz: Optional timezone to translate timestamps to
        :param series_format: Optional desired format for the series
        """
        if series_format is None:
            if his_ops.HAVE_PANDAS:
                series_format = self._HIS_READ_SERIES_OPERATION.FORMAT_SERIES
            else:
                series_format = self._HIS_READ_SERIES_OPERATION.FORMAT_LIST

        op = self._HIS_READ_SERIES_OPERATION(self, point, rng, tz, series_format)
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    def his_write_series(self, point, series, tz=None, callback=None):
        """
        Write the historical data of the given point.

        :param point: Haystack 'point' entity to read the data from
        :param series: Historical series data to write
        :param tz: Optional timezone to translate timestamps to
        """
        op = self._HIS_WRITE_SERIES_OPERATION(self, point, series, tz)
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    def his_read_frame(self, columns, rng, tz=None, frame_format=None, callback=None):
        """
        Read the historical data of multiple given points and return
        them as a data frame.

        :param columns: A list of Haystack 'point' instances or a dict mapping
                        the column label to the Haystack 'point' instance.
        :param rng: Historical read range for the 'point'
        :param tz: Optional timezone to translate timestamps to
        :param frame_format: Optional desired format for the data frame
        """
        if frame_format is None:
            if his_ops.HAVE_PANDAS:
                frame_format = self._HIS_READ_FRAME_OPERATION.FORMAT_FRAME
            else:
                frame_format = self._HIS_READ_FRAME_OPERATION.FORMAT_LIST

        op = self._HIS_READ_FRAME_OPERATION(self, columns, rng, tz, frame_format)
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    def his_write_frame(self, frame, columns=None, tz=None, callback=None):
        """
        Write the historical data of multiple given points.

        :param frame: Data frame to write to.  Columns either list explicit
                        entity IDs or column aliases which are mapped in the
                        columns parameter.
        :param columns: If frame does not list explicit IDs, this should be a
                        dict mapping the column names to either entity IDs or
                        entity instances.
        :param tz: Reference timestamp to use for writing, default is UTC.
        """
        op = self._HIS_WRITE_FRAME_OPERATION(self, columns, frame, tz)
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    @property
    def site(self):
        """
        This helper will return the first site found on the server.
        This case is typical : having one site per server.
        """
        sites = self.find_entity("site").result
        return sites[list(sites.keys())[0]]

    @property
    def sites(self):
        """
        This helper will return all sites found on the server.
        """
        sites = self.find_entity("site").result
        return sites

    # Extension feature support.
    FEATURE_HISREAD_MULTI = "hisRead/multi"  # Multi-point hisRead
    FEATURE_HISWRITE_MULTI = "hisWrite/multi"  # Multi-point hisWrite
    FEATURE_ID_UUID = "id_uuid"

    def has_features(self, features, cache=True, callback=None):
        """
        Determine if a given feature is supported.  This is a helper function
        for determining if the server implements a given feature.  The feature
        is given as a string in the form of "base_feature/extension".

        Result is a dict of features and the states (boolean).

        :param features: Features to check for.
        """
        op = self._HAS_FEATURES_OPERATION(self, features, cache=cache)
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    # Protected methods/properties

    def _on_about(self, cache, callback, **kwargs):
        return self._get_grid("about", callback, cache=cache, **kwargs)

    def _on_ops(self, cache, callback, **kwargs):
        return self._get_grid("ops", callback, cache=cache, **kwargs)

    def _on_formats(self, cache, callback, **kwargs):
        return self._get_grid("formats", callback, cache=cache, **kwargs)

    def _on_read(self, ids, filter_expr, limit, callback, **kwargs):
        if isinstance(ids, string_types) or isinstance(ids, hszinc.Ref):
            # Make sure we always pass a list.
            ids = [ids]

        if bool(ids):
            if filter_expr is not None:
                raise ValueError("Either specify ids or filter_expr, not both")

            ids = [self._obj_to_ref(r) for r in ids]

            if len(ids) == 1:
                # Reading a single entity
                return self._get_grid("read", callback, args={"id": ids[0]}, **kwargs)
            else:
                # Reading several entities
                grid = hszinc.Grid()
                grid.column["id"] = {}
                grid.extend([{"id": r} for r in ids])
                return self._post_grid("read", grid, callback, **kwargs)
        else:
            args = {"filter": filter_expr}
            if limit is not None:
                args["limit"] = int(limit)

            return self._get_grid("read", callback, args=args, **kwargs)

    def _on_nav(self, nav_id, callback, **kwargs):
        return self._get_grid("nav", callback, args={"nav_id": nav_id}, **kwargs)

    def _on_watch_sub(self, points, watch_id, watch_dis, lease, callback, **kwargs):
        grid = hszinc.Grid()
        grid.column["id"] = {}
        grid.extend([{"id": self._obj_to_ref(p)} for p in points])
        if watch_id is not None:
            grid.metadata["watchId"] = watch_id
        if watch_dis is not None:
            grid.metadata["watchDis"] = watch_dis
        if lease is not None:
            grid.metadata["lease"] = lease
        return self._post_grid("watchSub", grid, callback, **kwargs)

    def _on_watch_unsub(self, watch, points, callback, **kwargs):
        grid = hszinc.Grid()
        grid.column["id"] = {}

        if not isinstance(watch, string_types):
            watch = watch.id
        grid.metadata["watchId"] = watch

        if points is not None:
            grid.extend([{"id": self._obj_to_ref(p)} for p in points])
        else:
            grid.metadata["close"] = hszinc.MARKER
        return self._post_grid("watchSub", grid, callback, **kwargs)

    def _on_watch_poll(self, watch, refresh, callback, **kwargs):
        grid = hszinc.Grid()
        grid.column["empty"] = {}

        if not isinstance(watch, string_types):
            watch = watch.id
        grid.metadata["watchId"] = watch
        return self._post_grid("watchPoll", grid, callback, **kwargs)

    def _on_point_write(self, point, level, val, who, duration, callback, **kwargs):
        args = {"id": self._obj_to_ref(point)}
        if level is None:
            if (val is not None) or (who is not None) or (duration is not None):
                raise ValueError(
                    "If level is None, val, who and duration must " "be None too."
                )
        else:
            args.update({"level": level, "val": val})
            if who is not None:
                args["who"] = who
            if duration is not None:
                args["duration"] = duration
        return self._get_grid("pointWrite", callback, args=args, **kwargs)
        # Won't work in for nhaystack... putting that on old
        # return self._post_grid("pointWrite", grid_ops.dict_to_grid(args), callback, expect_format=hszinc.MODE_ZINC, args=args, **kwargs)

    def _on_his_read(self, point, rng, callback, **kwargs):
        if isinstance(rng, slice):
            str_rng = ",".join([hszinc.dump_scalar(p) for p in (rng.start, rng.stop)])
        elif not isinstance(rng, string_types):
            str_rng = hszinc.dump_scalar(rng)
        else:
            # Better be valid!
            # str_rng = rng
            str_rng = hszinc.dump_scalar(rng, mode=hszinc.MODE_ZINC)

        return self._get_grid(
            "hisRead",
            callback,
            args={"id": self._obj_to_ref(point), "range": str_rng},
            **kwargs
        )

    def _on_his_write(
        self, point, timestamp_records, callback, post_format=hszinc.MODE_ZINC, **kwargs
    ):
        grid = hszinc.Grid()
        grid.metadata["id"] = self._obj_to_ref(point)
        grid.column["ts"] = {}
        grid.column["val"] = {}

        if hasattr(timestamp_records, "to_dict"):
            timestamp_records = timestamp_records.to_dict()

        timestamp_records = list(timestamp_records.items())
        timestamp_records.sort(key=lambda rec: rec[0])
        for (ts, val) in timestamp_records:
            grid.append({"ts": ts, "val": val})

        return self._post_grid(
            "hisWrite", grid, callback, post_format=post_format, **kwargs
        )

    def _on_invoke_action(
        self,
        entity,
        action,
        callback,
        action_args,
        post_format=hszinc.MODE_ZINC,
        **kwargs
    ):
        grid = hszinc.Grid()
        grid.metadata["id"] = self._obj_to_ref(entity)
        grid.metadata["action"] = action
        for arg in action_args.keys():
            grid.column[arg] = {}
        grid.append(action_args)

        return self._post_grid(
            "invokeAction", grid, callback, post_format=post_format, **kwargs
        )

    def _get(self, uri, callback, api=True, **kwargs):
        """
        Perform a raw HTTP GET operation.  This is a convenience wrapper around
        the HTTP client class that allows pre/post processing of the request by
        the session instance.
        """
        if api:
            uri = "%s/%s" % (self._api_dir, uri)
        return self._client.get(uri, callback, **kwargs)

    def _get_grid(self, uri, callback, expect_format=None, cache=False, **kwargs):
        """
        Perform a HTTP GET of a grid.
        """
        if expect_format is None:
            expect_format = self._grid_format
        op = self._GET_GRID_OPERATION(
            self, uri, expect_format=expect_format, cache=cache, **kwargs
        )
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    def _post(
        self,
        uri,
        callback,
        body=None,
        body_type=None,
        body_size=None,
        headers=None,
        api=True,
        **kwargs
    ):
        """
        Perform a raw HTTP POST operation.  This is a convenience wrapper around
        the HTTP client class that allows pre/post processing of the request by
        the session instance.
        """
        if api:
            uri = "%s/%s" % (self._api_dir, uri)
        return self._client.post(
            uri=uri,
            callback=callback,
            body=body,
            body_type=body_type,
            body_size=body_size,
            headers=headers,
            **kwargs
        )

    def _post_grid(
        self, uri, grid, callback, post_format=None, expect_format=None, **kwargs
    ):
        """
        Perform a HTTP POST of a grid.
        """
        if expect_format is None:
            expect_format = self._grid_format
        if post_format is None:
            post_format = self._grid_format
        op = self._POST_GRID_OPERATION(
            self,
            uri,
            grid,
            expect_format=expect_format,
            post_format=post_format,
            **kwargs
        )
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    def _obj_to_ref(self, obj):
        """
        Convert an arbitrary object referring to an entity to an entity
        reference.
        """
        if isinstance(obj, hszinc.Ref):
            return obj
        if isinstance(obj, string_types):
            return hszinc.Ref(obj)
        if hasattr(obj, "id"):
            return obj.id
        raise NotImplementedError(
            "Don't know how to get the ID from a %s" % obj.__class__.__name__
        )

    # Private methods/properties

    def _on_authenticate_done(self, operation, **kwargs):
        """
        Process the result of an authentication operation.  This needs to be
        implemented in the subclass and should, at minimum, set a flag in the
        subclass to indicate the authentication state and clear the _auth_op
        attribute on the base class.
        """
        raise NotImplementedError("To be implemented in %s" % self.__class__.__name__)

    def config_pint(self, value=False):
        if value:
            self._use_pint = True
        else:
            self._use_pint = False
        hszinc.use_pint(self._use_pint)

    def logout(self):
        raise NotImplementedError("Must be defined depending on each implementation")

    def __enter__(self):
        """Entering context manager

        usage:
        with WhateverSession(uri, username, password, **kwargs) as session:
            # do whatever with session

        """

        return self

    def __exit__(self, _type, value, traceback):
        """On exit, call the logout procedure defined in the class"""
        self.logout()
