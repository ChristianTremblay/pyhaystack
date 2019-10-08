#!python
# -*- coding: utf-8 -*-
"""
VRT Widesky low-level multi-hisRead/hisWrite operation mix-in.  This is a
mix-in for HaystackSession that implements CRUD operations as used in VRT
Widesky's implementation of Project Haystack.

At present, this has not been adopted by other implementations.
"""

import hszinc
from six import string_types


class MultiHisOpsMixin(object):
    """
    The Multi-His operations mix-in implements low-level support for
    multi-point hisRead and hisWrite operations.
    """

    def multi_his_read(self, points, rng, callback=None):
        """
        Read the historical data for multiple points.  This processes each
        point given by the list points and returns the data from that point in
        a numbered column named idN where N starts counting from zero.
        """
        if isinstance(rng, slice):
            str_rng = ",".join([hszinc.dump_scalar(p) for p in (rng.start, rng.stop)])
        elif not isinstance(rng, string_types):
            str_rng = hszinc.dump_scalar(rng)
        else:
            # Better be valid!
            str_rng = rng

        args = {"range": str_rng}
        for (col, point) in enumerate(points):
            args["id%d" % col] = self._obj_to_ref(point)

        return self._get_grid("hisRead", callback, args=args)

    def multi_his_write(self, timestamp_records, callback=None):
        """
        Write the historical data for multiple points.

        timestamp_records may be given as:
        - a Pandas DataFrame object, with column names specifying IDs of points
        - a list of dicts with the key 'ts' mapping to a datetime object and
          the remaining keys mapping point IDs to the values to be written.
        - a dict of dicts, with the outer dict mapping timestamps to
          the inner dict mapping point IDs to values.
        """
        # Grid
        grid = hszinc.Grid()
        grid.column["ts"] = {}

        # A mapping of IDs to column indexes
        point_idx = {}

        def _get_idx(point_id):
            try:
                return point_idx[point_id]
            except KeyError:
                col = len(point_idx)
                point_idx[point_id] = col
                grid.column["v%d" % col] = {"id": self._obj_to_ref(point_id)}
                return col

        # Collate the grid data by timestamp.
        grid_data_by_ts = {}

        def _get_ts(ts):
            try:
                ts_rec = grid_data_by_ts[ts]
            except KeyError:
                ts_rec = {"ts": ts}
                grid_data_by_ts[ts] = ts_rec
            return ts_rec

        if hasattr(timestamp_records, "to_dict"):
            # Probably a Pandas DataFrame.  Assume it returns
            # {column: {ts: value}}
            for point_id, col_data in timestamp_records.to_dict().items():
                col_idx = _get_idx(point_id)
                col = "v%d" % col_idx
                for ts, value in col_data.items():
                    ts_rec = _get_ts(ts)
                    ts_rec[col] = value
        elif isinstance(timestamp_records, dict):
            # A dict of dicts.
            for ts, values in timestamp_records.items():
                ts_rec = _get_ts(ts)
                for point_id, value in values.items():
                    col_idx = _get_idx(point_id)
                    ts_rec["v%d" % col_idx] = value
        else:
            # A list of dicts, I hope!
            for rec in timestamp_records:
                ts = rec.pop("ts")
                ts_rec = _get_ts(ts)
                for point_id, value in rec.items():
                    col_idx = _get_idx(point_id)
                    ts_rec["v%d" % col_idx] = value

        # Fill up the grid
        grid.extend(sorted(grid_data_by_ts.values(), key=lambda r: r["ts"]))

        # Submit the data
        return self._post_grid("hisWrite", grid, callback)
