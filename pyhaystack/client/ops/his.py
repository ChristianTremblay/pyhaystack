#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
High-level history functions.  These wrap the basic his_read function to allow
some alternate representations of the historical data.
"""

import hszinc
import fysom
import pytz

from datetime import tzinfo
from six import string_types
from ...util import state
from ...util.asyncexc import AsynchronousException

try:
    from pandas import Series, DataFrame
    HAVE_PANDAS = True
except ImportError: # pragma: no cover
    # Not covered, since we'll always have 'pandas' available during tests.
    HAVE_PANDAS = False


def _resolve_tz(tz):
    """
    Resolve a given timestamp.
    """
    if (tz is None) or isinstance(tz, tzinfo):
        return tz
    if isinstance(tz, string_types):
        if '/' in tz:
            # Olson database name
            return pytz.timezone(tz)
        else:
            return hszinc.zoneinfo.timezone(tz)


class HisReadSeriesOperation(state.HaystackOperation):
    """
    Read the series data from a 'point' entity and present it in a concise
    format.
    """

    FORMAT_LIST     = 'list'    # [(ts1, value1), (ts2, value2), ...]
    FORMAT_DICT     = 'dict'    # {ts1: value1, ts2: value2, ...}
    FORMAT_SERIES   = 'series'  # pandas.Series

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

        if series_format not in (self.FORMAT_LIST, self.FORMAT_DICT,
                self.FORMAT_SERIES):
            raise ValueError('Unrecognsied series_format %s' % series_format)

        if (series_format == self.FORMAT_SERIES) and (not HAVE_PANDAS):
            raise NotImplementedError('pandas not available.')

        self._session = session
        self._point = point
        self._range = rng
        self._tz = _resolve_tz(tz)
        self._series_format = series_format

        self._state_machine = fysom.Fysom(
                initial='init', final='done',
                events=[
                    # Event             Current State       New State
                    ('go',              'init',             'read'),
                    ('read_done',       'read',             'done'),
                    ('exception',       '*',                'done'),
                ], callbacks={
                    'onenterread':          self._do_read,
                    'onenterdone':          self._do_done,
                })

    def go(self):
        self._state_machine.go()

    def _do_read(self, event):
        """
        Request the data from the server.
        """
        self._session.his_read(point=self._point, rng=self._range,
                callback=self._on_read)

    def _on_read(self, operation, **kwargs):
        """
        Process the grid, format it into the requested format.
        """
        try:
            # See if the read succeeded.
            grid = operation.result

            if self._tz is None:
                conv_ts = lambda ts : ts
            else:
                conv_ts = lambda ts : ts.astimezone(self._tz)

            # Convert grid to list of tuples
            data = [(conv_ts(row['ts']), row['val']) for row in grid]

            if self._series_format == self.FORMAT_DICT:
                data = dict(data)
            elif self._series_format == self.FORMAT_SERIES:
                # Split into index and data.
                (index, data) = zip(*data)
                data = Series(data=data, index=index)

            self._state_machine.read_done(result=data)
        except: # Catch all exceptions to pass to caller.
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

    FORMAT_LIST     = 'list'    # [{'ts': ts1, 'col1': val1, ...}, {...}, ...]
    FORMAT_DICT     = 'dict'    # {ts1: {'col1': val1, ...}, ts2: ...}
    FORMAT_FRAME    = 'frame'   # pandas.DataFrame

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
        self._log = session._log.getChild('his_read_frame')

        if frame_format not in (self.FORMAT_LIST, self.FORMAT_DICT,
                self.FORMAT_FRAME):
            raise ValueError('Unrecognsied frame_format %s' % frame_format)

        if (frame_format == self.FORMAT_FRAME) and (not HAVE_PANDAS):
            raise NotImplementedError('pandas not available.')

        # Convert the columns to a list of tuples.
        strip_ref = lambda r : r.name if isinstance(r, hszinc.Ref) else r
        if isinstance(columns, dict):
            # Ensure all are strings to references
            columns = [(str(c),strip_ref(r)) for c, r in columns.items()]
        else:
            # Translate to a dict:
            columns = [(strip_ref(c), c) for c in columns]

        self._session = session
        self._columns = columns
        self._range = rng
        self._tz = _resolve_tz(tz)
        self._frame_format = frame_format
        self._data_by_ts = {}
        self._todo = set([c[0] for c in columns])

        self._state_machine = fysom.Fysom(
                initial='init', final='done',
                events=[
                    # Event             Current State       New State
                    ('do_multi_read',   'init',             'multi_read'),
                    ('all_read_done',   'multi_read',       'postprocess'),
                    ('do_single_read',  'init',             'single_read'),
                    ('all_read_done',   'single_read',      'postprocess'),
                    ('process_done',    'postprocess',      'done'),
                    ('exception',       '*',                'done'),
                ], callbacks={
                    'onentermulti_read':    self._do_multi_read,
                    'onentersingle_read':   self._do_single_read,
                    'onenterpostprocess':   self._do_postprocess,
                    'onenterdone':          self._do_done,
                })

    def go(self):
        if hasattr(self._session, 'multi_his_read'):
            # Session object supports multi-his-read
            self._log.debug('Using multi-his-read support')
            self._state_machine.do_multi_read()
        else:
            # Emulate multi-his-read with separate
            self._log.debug('No multi-his-read support, emulating')
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
        self._session.multi_his_read(points=[c[1] for c in self._columns],
                rng=self._range, callback=self._on_multi_read)

    def _on_multi_read(self, operation, **kwargs):
        """
        Handle the multi-valued grid.
        """
        try:
            grid = operation.result

            if self._tz is None:
                conv_ts = lambda ts : ts
            else:
                conv_ts = lambda ts : ts.astimezone(self._tz)

            for row in grid:
                ts = conv_ts(row['ts'])
                rec = self._get_ts_rec(ts)
                for (col_idx, (col, _)) in enumerate(self._columns):
                    val = row.get('v%d' % col_idx)
                    if (val is not None) or \
                            (self._frame_format != self.FORMAT_FRAME):
                        rec[col] = val
            self._state_machine.all_read_done()
        except: # Catch all exceptions to pass to caller.
            self._log.debug('Hit exception', exc_info=1)
            self._state_machine.exception(result=AsynchronousException())

    def _do_single_read(self, event):
        """
        Request the data from the server as multiple single-read requests.
        """
        for col, point in self._columns:
            self._log.debug('Column %s point %s', col, point)
            self._session.his_read(point, self._range,
                    lambda operation, **kw : self._on_single_read(operation,
                        col=col))

    def _on_single_read(self, operation, col, **kwargs):
        """
        Handle the multi-valued grid.
        """
        self._log.debug('Response back for column %s', col)
        try:
            grid = operation.result

            if self._tz is None:
                conv_ts = lambda ts : ts
            else:
                conv_ts = lambda ts : ts.astimezone(self._tz)

            for row in grid:
                ts = conv_ts(row['ts'])
                if self._tz is None:
                    self._tz = ts.tzinfo

                rec = self._get_ts_rec(ts)
                val = row.get('val')
                if (val is not None) or \
                        (self._frame_format != self.FORMAT_FRAME):
                    rec[col] = val

            self._todo.discard(col)
            self._log.debug('Still waiting for: %s', self._todo)
            if not self._todo:
                # No more to read
                self._state_machine.all_read_done()
        except: # Catch all exceptions to pass to caller.
            self._log.debug('Hit exception', exc_info=1)
            self._state_machine.exception(result=AsynchronousException())

    def _do_postprocess(self, event):
        """
        Convert the dict-of-dicts to the desired frame format.
        """
        self._log.debug('Post-processing')
        try:
            if self._frame_format == self.FORMAT_LIST:
                def _merge_ts(item):
                    rec = item[1].copy()
                    rec['ts'] = item[0]
                    return rec
                data = list(map(_merge_ts, list(self._data_by_ts.items())))
            elif self._frame_format == self.FORMAT_FRAME:
                index = list(self._data_by_ts.keys())
                values = list(self._data_by_ts.values())
                data = DataFrame(index=index, data=values)
            else:
                data = self._data_by_ts
            self._state_machine.process_done(result=data)
        except: # Catch all exceptions to pass to caller.
            self._log.debug('Hit exception', exc_info=1)
            self._state_machine.exception(result=AsynchronousException())

    def _do_done(self, event):
        """
        Return the result from the state machine.
        """
        self._done(event.result)
