#!python
# -*- coding: utf-8 -*-
"""
point.py: Implementation of a datapoint in Project Haystack
"""

import hszinc
import time
import logging
import datetime

from ..history.HisRecord import HisRecord
from ..util.tools import isfloat, isBool

class HaystackPoint(object):
    """
    The point class acts as a container for entity metadata and provides an
    interface for conveniently accessing the point's real-time and historical
    data.
    """

    def __init__(self, session, point_id, meta=None):
        """
        Create a point that references some Haystack entity.
        """
        self._session   = session
        self._point_id  = point_id
        self._log       = session._log.getChild('pt.%s' % point_id)

        # We do lazy evaluation on the point metadata.
        self._meta      = None
        self._meta_expiry = 0

        if meta is not None:
            self._load_meta(meta)

    def __repr__(self):
        """
        Dump a rough representation of the point.
        """
        return '%s(%r, %r)' % (self.__class__.__name__,
                self._session, self._point_id)

    @property
    def _refresh_due(self):
        """
        Return True if a refresh is due.
        """
        return (self._meta_expiry <= time.time())

    def _refresh_meta(self, force=False):
        """
        Retrieve the metadata from the server if out of date.
        """
        if not (force or self._refresh_due):
            # We're not being forced and the refresh isn't due yet.
            return

        meta = self._session._get_grid('read', \
                id=hszinc.dump_scalar(hszinc.Ref(self._point_id)))
        self._load_meta(meta[0])

    def _load_meta(self, meta):
        """
        Store the metadata loaded from elsewhere and re-set the expiry timer.
        """
        meta_id = meta.pop('id',None)
        if meta_id is None:
            raise ValueError('Point %s no longer exists' % self._point_id)
        elif meta_id.name != self._point_id:
            raise ValueError('Metadata for incorrect point (%s vs %s)' \
                    % (meta_id.name, self._point_id))

        self._meta = meta
        self._meta_expiry = time.time() + 300.0 # TODO: define this

    def _localise_dt(self, dt):
        """
        Localise a datetime object for this timezone.
        """
        if not isinstance(dt, datetime.datetime):
            raise TypeError('%r is not a datetime.datetime' % dt)

        if dt.tzinfo is None:
            return self.tz.localize(dt)
        else:
            return dt.astimezone(self.tz)

    # Metadata access routines.

    @property
    def meta(self):
        """
        Return a copy of the point's metadata.
        """
        self._refresh_meta()
        return self._meta.copy()

    def get_meta(self, key):
        """
        Return the value of a given metadata key.
        """
        self._refresh_meta()
        return self._meta[key]

    def has_meta(self, key):
        """
        Return the presence of a key in the metadata.
        """
        self._refresh_meta()
        return (key in self._meta)

    @property
    def id(self):
        return self._point_id

    @property
    def tz_name(self):
        """
        Return the timezone name for this point.
        """
        return self.get_meta('tz')

    @property
    def tz(self):
        """
        Return the timezone for this point.
        """
        return hszinc.zoneinfo.timezone(self.tz_name)

    def __getattr__(self, attr):
        """
        Convenience helper for retrieval of attributes.
        """
        try:
            return self.__dict__[attr]
        except KeyError:
            try:
                self._refresh_meta()
                return self.__dict__['_meta'][attr]
            except KeyError:
                raise AttributeError(attr)

    # Historical data access

    def his_read(self, start=None, end=None, rng=None):
        """
        Read historical data for this data point.
        """
        if not self.has_meta('his'):
            raise NotImplementedError('%s does not implement history' \
                    % self._point_id)

        # Build datetimeRange based on start and end
        if (start is not None) or (end is not None):
            if start is None:
                raise ValueError('start requires end')
            if end is None:
                raise ValueError('end requires start')
            if rng is not None:
                raise ValueError('rng and start/end are mutually exclusive')
            rng = (start, end)
        elif rng is None:
            raise ValueError('start and end or rng is required')

        return HisRecord(self._session, self._point_id, rng)

    def his_write(self, records):
        """
        Write historical data to this data point.  records should be a list of
        dicts with the following keys:

        - ts: a datetime.datetime object with the timestamp of the reading.
        - val: the value to be written at that time.
        """
        if not self.has_meta('his'):
            raise NotImplementedError('%s does not implement history' \
                    % self._point_id)

        if isinstance(records, dict):
            records = [records]

        grid = hszinc.Grid()
        grid.metadata['id'] = hszinc.Ref(self._point_id)
        grid.column['ts'] = {}
        grid.column['val'] = {}
        grid.extend([
            {'ts': self._localise_dt(r['ts']), 'val': r['val']}
            for r in records
        ])
        self._session._post_grid('hisWrite', grid)

    def __getitem__(self, rng):
        """
        Perform a historical read of this point at the given time.  This is
        provided as a syntactic convenience.

        If a slice object is given (start:stop syntax) the start and stop
        attributes specify the start and end.  Beware: Haystack conventions
        differ to that of normal Python conventions.

        Otherwise, the parameter is taken as a raw range.
        """
        if isinstance(rng, slice):
            # Correction needed as the request was build :
            # &range=<member+%27start%27+of+%27slice%27+objects>%2C<member+%27stop%27+of+%27slice%27+objects>
            start, stop, step = rng.indices(len(self))
            return self.his_read(start=start, end=stop)
        return self.his_read(rng=rng)

    def __setitem__(self, ts, value):
        """
        Perform a historical write of this point at the given time.  This is
        a very slow way to import lots of data, but is useful for occasional
        writes.  For bulk inserts, see `his_write`.
        """
        return self.his_write({'ts': ts, 'val': value})

    @property
    def value(self):
        if isBool(self.curVal):
            return self.curVal
        elif isinstance(self.curVal, hszinc.Quantity):
            return float(self.curVal)
        else:
            raise ValueError("Don't know what to return")


