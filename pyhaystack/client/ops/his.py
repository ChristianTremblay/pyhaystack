#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
High-level history functions.  These wrap the basic his_read function to allow
some alternate representations of the historical data.
"""

import hszinc
import fysom
import pytz
from copy import deepcopy

from datetime import tzinfo
from six import string_types
from ...util import state
from ...util.asyncexc import AsynchronousException

try:
    from pandas import Series, DataFrame

    HAVE_PANDAS = True
except ImportError:  # pragma: no cover
    # Not covered, since we'll always have 'pandas' available during tests.
    HAVE_PANDAS = False


def _resolve_tz(tz):
    """
    Resolve a given timestamp.
    """
    if (tz is None) or isinstance(tz, tzinfo):
        return tz
    if isinstance(tz, string_types):
        if "/" in tz:
            # Olson database name
            return pytz.timezone(tz)
        else:
            return hszinc.zoneinfo.timezone(tz)


class HisReadSeriesOperation(state.HaystackOperation):
    """
    Read the series data from a 'point' entity and present it in a concise
    format.
    """

    FORMAT_LIST = "list"  # [(ts1, value1), (ts2, value2), ...]
    FORMAT_DICT = "dict"  # {ts1: value1, ts2: value2, ...}
    FORMAT_SERIES = "series"  # pandas.Series

    def __init__(self, session, point, rng, tz, series_format):
        """
        Read the series data and return it.

        :param session: Haystack HTTP session object.
        :param point: ID of historical 'point' object to read.
        :param rng: Range to read from 'point'
        :param tz: Timezone to translate timezones to.  May be None.
        :param series_format: What format to present the series in.
        """
        super(HisReadSeriesOperation, self).__init__()

        if series_format not in (
            self.FORMAT_LIST,
            self.FORMAT_DICT,
            self.FORMAT_SERIES,
        ):
            raise ValueError("Unrecognised series_format %s" % series_format)

        if (series_format == self.FORMAT_SERIES) and (not HAVE_PANDAS):
            raise NotImplementedError("pandas not available.")

        if isinstance(rng, slice):
            rng = ",".join(
                [
                    hszinc.dump_scalar(p, mode=hszinc.MODE_ZINC)
                    for p in (rng.start, rng.stop)
                ]
            )

        self._session = session
        self._point = point
        self._range = rng
        self._tz = _resolve_tz(tz)
        self._series_format = series_format

        self._state_machine = fysom.Fysom(
            initial="init",
            final="done",
            events=[
                # Event             Current State       New State
                ("go", "init", "read"),
                ("read_done", "read", "done"),
                ("exception", "*", "done"),
            ],
            callbacks={"onenterread": self._do_read, "onenterdone": self._do_done},
        )

    def go(self):
        self._state_machine.go()

    def _do_read(self, event):
        """
        Request the data from the server.
        """
        self._session.his_read(
            point=self._point, rng=self._range, callback=self._on_read
        )

    def _on_read(self, operation, **kwargs):
        """
        Process the grid, format it into the requested format.
        """
        try:
            # See if the read succeeded.
            operation.wait
            grid = operation.result

            if self._tz is None:
                conv_ts = lambda ts: ts
            else:
                conv_ts = lambda ts: ts.astimezone(self._tz)

            # Convert grid to list of tuples
            data = [(conv_ts(row["ts"]), row["val"]) for row in grid]

            units = ""
            values = []
            if self._series_format == self.FORMAT_DICT:
                data = dict(data)
            elif self._series_format == self.FORMAT_SERIES:
                # Split into index and data.
                try:
                    (index, data) = zip(*data)
                    if isinstance(data[0], hszinc.Quantity) or isinstance(
                        data[-1], hszinc.Quantity
                    ):
                        for each in data:
                            try:
                                values.append(each.value)
                                if units == "":
                                    units = each.unit
                            except AttributeError:
                                if isinstance(each, float):
                                    values.append(each)
                                continue
                    else:
                        values = data
                except ValueError:
                    values = []
                    index = []
                    units = ""

                # ser = Series(data=data[0].value, index=index)
                meta_serie = MetaSeries(data=values, index=index)
                meta_serie.add_meta("units", units)
                meta_serie.add_meta("point", self._point)

            self._state_machine.read_done(result=meta_serie)
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _do_done(self, event):
        """
        Return the result from the state machine.
        """
        self._done(event.result)


class HisReadFrameOperation(state.HaystackOperation):
    """
    Read the series data from several 'point' entities and present them in a
    concise format.
    """

    FORMAT_LIST = "list"  # [{'ts': ts1, 'col1': val1, ...}, {...}, ...]
    FORMAT_DICT = "dict"  # {ts1: {'col1': val1, ...}, ts2: ...}
    FORMAT_FRAME = "frame"  # pandas.DataFrame

    def __init__(self, session, columns, rng, tz, frame_format):
        """
        Read the series data and return it.

        :param session: Haystack HTTP session object.
        :param columns: IDs of historical point objects to read.
        :param rng: Range to read from 'point'
        :param tz: Timezone to translate timezones to.  May be None.
        :param frame_format: What format to present the frame in.
        """
        super(HisReadFrameOperation, self).__init__()
        self._log = session._log.getChild("his_read_frame")

        if frame_format not in (self.FORMAT_LIST, self.FORMAT_DICT, self.FORMAT_FRAME):
            raise ValueError("Unrecognised frame_format %s" % frame_format)

        if (frame_format == self.FORMAT_FRAME) and (not HAVE_PANDAS):
            raise NotImplementedError("pandas not available.")

        if isinstance(rng, slice):
            rng = ",".join(
                [
                    hszinc.dump_scalar(p, mode=hszinc.MODE_ZINC)
                    for p in (rng.start, rng.stop)
                ]
            )

        # Convert the columns to a list of tuples.
        strip_ref = lambda r: r.name if isinstance(r, hszinc.Ref) else r
        if isinstance(columns, dict):
            # Ensure all are strings to references
            columns = [(str(c), strip_ref(r)) for c, r in columns.items()]
        else:
            # Translate to a dict:
            columns = [(strip_ref(c), c) for c in columns]

        self._session = session
        self._columns = columns
        self._range = hszinc.dump_scalar(rng, mode=hszinc.MODE_ZINC)
        self._tz = _resolve_tz(tz)
        self._frame_format = frame_format
        self._data_by_ts = {}
        self._todo = set([c[0] for c in columns])

        self._state_machine = fysom.Fysom(
            initial="init",
            final="done",
            events=[
                # Event             Current State       New State
                ("probe_multi", "init", "probing"),
                ("do_multi_read", "probing", "multi_read"),
                ("all_read_done", "multi_read", "postprocess"),
                ("do_single_read", "probing", "single_read"),
                ("all_read_done", "single_read", "postprocess"),
                ("process_done", "postprocess", "done"),
                ("exception", "*", "done"),
            ],
            callbacks={
                "onenterprobing": self._do_probe_multi,
                "onentermulti_read": self._do_multi_read,
                "onentersingle_read": self._do_single_read,
                "onenterpostprocess": self._do_postprocess,
                "onenterdone": self._do_done,
            },
        )

    def go(self):
        self._state_machine.probe_multi()

    def _do_probe_multi(self, event):
        self._log.debug("Probing for multi-his-read support")
        self._session.has_features(
            [self._session.FEATURE_HISREAD_MULTI], callback=self._on_probe_multi
        )

    def _on_probe_multi(self, operation, **kwargs):
        try:
            result = operation.result
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())
            return

        if result.get(self._session.FEATURE_HISREAD_MULTI):
            # Session object supports multi-his-read
            self._log.debug("Using multi-his-read support")
            self._state_machine.do_multi_read()
        else:
            # Emulate multi-his-read with separate
            self._log.debug("No multi-his-read support, emulating")
            self._state_machine.do_single_read()

    def _get_ts_rec(self, ts):
        try:
            return self._data_by_ts[ts]
        except KeyError:
            rec = {}
            self._data_by_ts[ts] = rec
            return rec

    def _do_multi_read(self, event):
        """
        Request the data from the server as a single multi-read request.
        """
        self._session.multi_his_read(
            points=[c[1] for c in self._columns],
            rng=self._range,
            callback=self._on_multi_read,
        )

    def _on_multi_read(self, operation, **kwargs):
        """
        Handle the multi-valued grid.
        """
        try:
            grid = operation.result

            if self._tz is None:
                conv_ts = lambda ts: ts
            else:
                conv_ts = lambda ts: ts.astimezone(self._tz)

            for row in grid:
                ts = conv_ts(row["ts"])
                rec = self._get_ts_rec(ts)
                for (col_idx, (col, _)) in enumerate(self._columns):
                    val = row.get("v%d" % col_idx)
                    if (val is not None) or (self._frame_format != self.FORMAT_FRAME):
                        rec[col] = val
            self._state_machine.all_read_done()
        except:  # Catch all exceptions to pass to caller.
            self._log.debug("Hit exception", exc_info=1)
            self._state_machine.exception(result=AsynchronousException())

    def _do_single_read(self, event):
        """
        Request the data from the server as multiple single-read requests.
        """
        for col, point in self._columns:
            self._log.debug("Column %s point %s", col, point)
            self._session.his_read(
                point,
                self._range,
                lambda operation, **kw: self._on_single_read(operation, col=col),
            )

    def _on_single_read(self, operation, col, **kwargs):
        """
        Handle the multi-valued grid.
        """
        self._log.debug("Response back for column %s", col)
        try:
            grid = operation.result

            if self._tz is None:
                conv_ts = lambda ts: ts
            else:
                conv_ts = lambda ts: ts.astimezone(self._tz)

            self._log.debug("%d records for %s: %s", len(grid), col, grid)
            for row in grid:
                ts = conv_ts(row["ts"])
                if self._tz is None:
                    self._tz = ts.tzinfo

                rec = self._get_ts_rec(ts)
                val = row.get("val")
                if (val is not None) or (self._frame_format != self.FORMAT_FRAME):
                    rec[col] = val

            self._todo.discard(col)
            self._log.debug("Still waiting for: %s", self._todo)
            if not self._todo:
                # No more to read
                self._state_machine.all_read_done()
        except:  # Catch all exceptions to pass to caller.
            self._log.debug("Hit exception", exc_info=1)
            self._state_machine.exception(result=AsynchronousException())

    def _do_postprocess(self, event):
        """
        Convert the dict-of-dicts to the desired frame format.
        """
        self._log.debug("Post-processing")
        try:
            if self._frame_format == self.FORMAT_LIST:

                def _merge_ts(item):
                    rec = item[1].copy()
                    rec["ts"] = item[0]
                    return rec

                data = list(map(_merge_ts, list(self._data_by_ts.items())))
                # print(data)
            elif self._frame_format == self.FORMAT_FRAME:
                # Build from dict
                data = MetaDataFrame.from_dict(self._data_by_ts, orient="index")

                def convert_quantity(val):
                    """
                    If value is Quantity, convert to value
                    """
                    if isinstance(val, hszinc.Quantity):
                        return val.value
                    else:
                        return val

                def get_units(serie):
                    try:
                        first_element = serie.dropna()[0]
                    except IndexError:  # needed for empty results
                        return ""
                    if isinstance(first_element, hszinc.Quantity):
                        return first_element.unit
                    else:
                        return ""

                for name, serie in data.iteritems():
                    """
                    Convert Quantity and put unit in metadata
                    """
                    data.add_meta(name, get_units(serie))
                    data[name] = data[name].apply(convert_quantity)

            else:
                data = self._data_by_ts
            self._state_machine.process_done(result=data)
        except:  # Catch all exceptions to pass to caller.
            self._log.debug("Hit exception", exc_info=1)
            self._state_machine.exception(result=AsynchronousException())

    def _do_done(self, event):
        """
        Return the result from the state machine.
        """
        self._done(event.result)


class HisWriteSeriesOperation(state.HaystackOperation):
    """
    Write the series data to a 'point' entity.
    """

    def __init__(self, session, point, series, tz):
        """
        Write the series data to the point.

        :param session: Haystack HTTP session object.
        :param point: ID of historical 'point' object to write.
        :param series: Series data to be written to the point.
        :param tz: If not None, a datetime.tzinfo instance for this write.
        """
        super(HisWriteSeriesOperation, self).__init__()

        # We've either been given an Entity instance or a string/reference
        # giving the name of an entity.
        if isinstance(point, string_types) or isinstance(point, hszinc.Ref):
            # We have the name of an entity, we'll need to fetch it.
            self._entity_id = point
            self._point = None
        else:
            # We have an entity.
            self._point = point
            self._entity_id = point.id

        self._session = session
        self._series = series
        self._tz = _resolve_tz(tz)

        self._state_machine = fysom.Fysom(
            initial="init",
            final="done",
            events=[
                # Event             Current State       New State
                ("have_tz", "init", "write"),
                ("have_point", "init", "get_point_tz"),
                ("need_point", "init", "get_point"),
                ("have_point", "get_point", "get_point_tz"),
                ("have_tz", "get_point_tz", "write"),
                ("need_equip", "get_point_tz", "get_equip"),
                ("have_equip", "get_equip", "get_equip_tz"),
                ("have_tz", "get_equip_tz", "write"),
                ("need_site", "get_equip_tz", "get_site"),
                ("have_site", "get_site", "get_site_tz"),
                ("have_tz", "get_site_tz", "write"),
                ("write_done", "write", "done"),
                ("exception", "*", "done"),
            ],
            callbacks={
                "onenterget_point": self._do_get_point,
                "onenterget_point_tz": self._do_get_point_tz,
                "onenterget_equip": self._do_get_equip,
                "onenterget_equip_tz": self._do_get_equip_tz,
                "onenterget_site": self._do_get_site,
                "onenterget_site_tz": self._do_get_site_tz,
                "onenterwrite": self._do_write,
                "onenterdone": self._do_done,
            },
        )

    def go(self):
        if self._tz is not None:  # Do we have a timezone?
            # We do!
            self._state_machine.have_tz()
        elif self._point is not None:  # Nope, do we have the point?
            # We do!
            self._state_machine.have_point()
        else:
            # We need to fetch the point to get its timezone.
            self._state_machine.need_point()

    def _do_get_point(self, event):
        """
        Retrieve the point entity.
        """
        self._session.get_entity(self._entity_id, single=True, callback=self._got_point)

    def _got_point(self, operation, **kwargs):
        """
        Process the return value from get_entity
        """
        try:
            self._point = operation.result
            self._state_machine.have_point()
        except:
            self._state_machine.exception(result=AsynchronousException())

    def _do_get_point_tz(self, event):
        """
        See if the point has a timezone?
        """
        if hasattr(self._point, "tz") and isinstance(self._point.tz, tzinfo):
            # We have our timezone.
            self._tz = self._point.tz
            self._state_machine.have_tz()
        else:
            # Nope, look at the equip then.
            self._state_machine.need_equip()

    def _do_get_equip(self, event):
        """
        Retrieve the equip entity.
        """
        self._point.get_equip(callback=self._got_equip)

    def _got_equip(self, operation, **kwargs):
        """
        Process the return value from get_entity
        """
        try:
            equip = operation.result
            self._state_machine.have_equip(equip=equip)
        except:
            self._state_machine.exception(result=AsynchronousException())

    def _do_get_equip_tz(self, event):
        """
        See if the equip has a timezone?
        """
        equip = event.equip
        if hasattr(equip, "tz") and isinstance(equip.tz, tzinfo):
            # We have our timezone.
            self._tz = equip.tz
            self._state_machine.have_tz()
        else:
            # Nope, look at the site then.
            self._state_machine.need_site()

    def _do_get_site(self, event):
        """
        Retrieve the site entity.
        """
        self._point.get_site(callback=self._got_site)

    def _got_site(self, operation, **kwargs):
        """
        Process the return value from get_entity
        """
        try:
            site = operation.result
            self._state_machine.have_site(site=site)
        except:
            self._state_machine.exception(result=AsynchronousException())

    def _do_get_site_tz(self, event):
        """
        See if the site has a timezone?
        """
        site = event.site
        if hasattr(site, "tz") and isinstance(site.tz, tzinfo):
            # We have our timezone.
            self._tz = site.tz
            self._state_machine.have_tz()
        else:
            try:
                # Nope, no idea then.
                raise ValueError(
                    "No timezone specified for operation, " "point, equip or site."
                )
            except:
                self._state_machine.exception(result=AsynchronousException())

    def _do_write(self, event):
        """
        Push the data to the server.
        """
        try:
            # Process the timestamp records into an appropriate format.
            if hasattr(self._series, "to_dict"):
                records = self._series.to_dict()
            elif not isinstance(self._series, dict):
                records = dict(self._series)
            else:
                records = self._series

            if not bool(records):
                # No data, skip writing this series.
                self._state_machine.write_done(result=None)
                return

            # Time-shift the records.
            if hasattr(self._tz, "localize"):
                localise = (
                    lambda ts: self._tz.localize(ts)
                    if ts.tzinfo is None
                    else ts.astimezone(self._tz)
                )
            else:
                localise = (
                    lambda ts: ts.replace(tzinfo=self._tz)
                    if ts.tzinfo is None
                    else ts.astimezone(self._tz)
                )
            records = dict([(localise(ts), val) for ts, val in records.items()])

            # Write the data
            self._session.his_write(
                point=self._entity_id,
                timestamp_records=records,
                callback=self._on_write,
            )
        except:
            self._state_machine.exception(result=AsynchronousException())

    def _on_write(self, operation, **kwargs):
        """
        Handle the write error, if any.
        """
        try:
            # See if the write succeeded.
            grid = operation.result
            if not isinstance(grid, hszinc.Grid):
                raise TypeError("Unexpected result: %r" % grid)
            # Move to the done state.
            self._state_machine.write_done(result=None)
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _do_done(self, event):
        """
        Return the result from the state machine.
        """
        self._done(event.result)


class HisWriteFrameOperation(state.HaystackOperation):
    """
    Write the series data to several 'point' entities.
    """

    def __init__(self, session, columns, frame, tz):
        """
        Write the series data.

        :param session: Haystack HTTP session object.
        :param columns: IDs of historical point objects to read.
        :param frame: Range to read from 'point'
        :param tz: Timezone to translate timezones to.
        """
        super(HisWriteFrameOperation, self).__init__()
        self._log = session._log.getChild("his_write_frame")

        tz = _resolve_tz(tz)
        if tz is None:
            tz = pytz.utc

        if hasattr(tz, "localize"):
            localise = (
                lambda ts: tz.localize(ts) if ts.tzinfo is None else ts.astimezone(tz)
            )
        else:
            localise = (
                lambda ts: ts.replace(tzinfo=tz)
                if ts.tzinfo is None
                else ts.astimezone(tz)
            )

        # Convert frame to list of records.
        if HAVE_PANDAS:
            # Convert Pandas frame to dict of dicts form.
            if isinstance(frame, DataFrame):
                self._log.debug("Convert from Pandas DataFrame")
                raw_frame = frame.to_dict(orient="dict")
                frame = {}
                for col, col_data in raw_frame.items():
                    for ts, val in col_data.items():
                        try:
                            frame_rec = frame[ts]
                        except KeyError:
                            frame_rec = {}
                            frame[ts] = frame_rec
                        frame[col] = val

        # Convert dict of dicts to records, de-referencing column names.
        if isinstance(frame, dict):
            if columns is None:

                def _to_rec(item):
                    (ts, raw_record) = item
                    record = raw_record.copy()
                    record["ts"] = ts
                    return record

            else:

                def _to_rec(item):
                    (ts, raw_record) = item
                    record = {}
                    for col, val in raw_record.items():
                        entity = columns[col]
                        if hasattr(entity, "id"):
                            entity = entity.id
                        if isinstance(entity, hszinc.Ref):
                            entity = entity.name
                        record[entity] = val

                    record["ts"] = ts
                    return record

            frame = list(map(_to_rec, list(frame.items())))
        elif columns is not None:
            # Columns are aliased.  De-alias the column names.
            frame = deepcopy(frame)
            for row in frame:
                ts = row.pop("ts")
                raw = row.copy()
                row.clear()
                row["ts"] = ts
                for column, point in columns.items():
                    try:
                        value = raw.pop(column)
                    except KeyError:
                        self._log.debug(
                            "At %s missing column %s (for %s): %s",
                            ts,
                            column,
                            point,
                            raw,
                        )
                        continue
                    row[session._obj_to_ref(point).name] = value

        # Localise all timestamps, extract columns:
        columns = set()

        def _localise_rec(r):
            r["ts"] = localise(r["ts"])
            columns.update(set(r.keys()) - set(["ts"]))
            return r

        frame = list(map(_localise_rec, frame))

        self._session = session
        self._frame = frame
        self._columns = columns
        self._todo = columns.copy()
        self._tz = _resolve_tz(tz)

        self._state_machine = fysom.Fysom(
            initial="init",
            final="done",
            events=[
                # Event             Current State       New State
                ("probe_multi", "init", "probing"),
                ("no_data", "init", "done"),
                ("do_multi_write", "probing", "multi_write"),
                ("all_write_done", "multi_write", "done"),
                ("do_single_write", "probing", "single_write"),
                ("all_write_done", "single_write", "done"),
                ("exception", "*", "done"),
            ],
            callbacks={
                "onenterprobing": self._do_probe_multi,
                "onentermulti_write": self._do_multi_write,
                "onentersingle_write": self._do_single_write,
                "onenterdone": self._do_done,
            },
        )

    def go(self):
        if not bool(self._columns):
            self._log.debug("No data to write")
            self._state_machine.no_data(result=None)
        else:
            self._state_machine.probe_multi()

    def _do_probe_multi(self, event):
        self._log.debug("Probing for multi-his-write support")
        self._session.has_features(
            [self._session.FEATURE_HISWRITE_MULTI], callback=self._on_probe_multi
        )

    def _on_probe_multi(self, operation, **kwargs):
        try:
            result = operation.result
        except:  # Catch all exceptions to pass to caller.
            self._log.warning("Unable to probe multi-his-write support", exc_info=1)
            self._state_machine.exception(result=AsynchronousException())
            result = {}
            return

        self._log.debug("Got result: %s", result)
        if result.get(self._session.FEATURE_HISWRITE_MULTI):
            # Session object supports multi-his-write
            self._log.debug("Using multi-his-write support")
            self._state_machine.do_multi_write()
        else:
            # Emulate multi-his-write with separate
            self._log.debug("No multi-his-write support, emulating")
            self._state_machine.do_single_write()

    def _do_multi_write(self, event):
        """
        Request the data from the server as a single multi-read request.
        """
        self._session.multi_his_write(self._frame, callback=self._on_multi_write)

    def _on_multi_write(self, operation, **kwargs):
        """
        Handle the multi-valued grid.
        """
        try:
            grid = operation.result
            if not isinstance(grid, hszinc.Grid):
                raise ValueError("Unexpected result %r" % grid)
            self._state_machine.all_write_done(result=None)
        except:  # Catch all exceptions to pass to caller.
            self._log.debug("Hit exception", exc_info=1)
            self._state_machine.exception(result=AsynchronousException())

    def _do_single_write(self, event):
        """
        Submit the data in single write requests.
        """
        for point in self._columns:
            self._log.debug("Point %s", point)

            # Extract a series for this column
            series = dict(
                [
                    (r["ts"], r[point])
                    for r in filter(lambda r: r.get(point) is not None, self._frame)
                ]
            )

            self._session.his_write_series(
                point,
                series,
                callback=lambda operation, **kw: self._on_single_write(
                    operation, point=point
                ),
            )

    def _on_single_write(self, operation, point, **kwargs):
        """
        Handle the single write.
        """
        self._log.debug("Response back for point %s", point)
        try:
            res = operation.result
            if res is not None:
                raise ValueError("Unexpected result %r" % res)

            self._todo.discard(point)
            self._log.debug("Still waiting for: %s", self._todo)
            if not self._todo:
                # No more to read
                self._state_machine.all_write_done(result=None)
        except:  # Catch all exceptions to pass to caller.
            self._log.debug("Hit exception", exc_info=1)
            self._state_machine.exception(result=AsynchronousException())

    def _do_done(self, event):
        """
        Return the result from the state machine.
        """
        self._done(event.result)


if HAVE_PANDAS:

    class MetaSeries(Series):
        """
        Custom Pandas Serie with meta data
        """

        meta = {}

        @property
        def _constructor(self):
            return MetaSeries

        def add_meta(self, key, value):
            self.meta[key] = value

    class MetaDataFrame(DataFrame):
        """
        Custom Pandas Dataframe with meta data
        Made from MetaSeries
        """

        meta = {}

        def __init__(self, *args, **kw):
            super(MetaDataFrame, self).__init__(*args, **kw)

        @property
        def _constructor(self):
            return MetaDataFrame

        _constructor_sliced = MetaSeries

        def add_meta(self, key, value):
            self.meta[key] = value
