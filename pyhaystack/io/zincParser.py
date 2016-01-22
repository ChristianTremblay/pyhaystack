# -*- coding: utf-8 -*-
"""
zincToJson allows to convert native haystack 'zinc'
format to Json when connecting to old Jace devices that
aren't able to generate Json response

As Json is easily handled in Python, it's the prefered syntax for web transactions
So everything is built with Json in mind.

It's a patch to support old devices

@author: CTremblay
"""
import json
import hszinc
import datetime

def zincToJson(req):
    # Parse the zinc text into grids
    grids = hszinc.parse(req)

    # Convert this back to a format that pyhaystack understands.
    # JSON grids have the following structure:
    # // JSON
    # {
    #   "meta": {"ver":"2.0", "projName":"test"},
    #   "cols":[
    #     {"name":"dis", "dis":"Equip Name"},
    #     {"name":"equip"},
    #     {"name":"siteRef"},
    #     {"name":"installed"}
    #   ],
    #   "rows":[
    #     {"dis":"RTU-1", "equip":"m:",
    #       "siteRef":"r:153c-699a HQ", "installed":"d:2005-06-01"},
    #     {"dis":"RTU-2", "equip":"m:",
    #       "siteRef":"r:153c-699a HQ", "installed":"d:999-07-12"}
    #   ]
    # }
    #
    # There is only support for one grid at a time.  Out of pure laziness on my
    # part, this does not convert scalar values to JSON format but rather, the
    # equivalent Python type.
    if len(grids) != 1:
        raise ValueError('Unable to handle result with %d grids' % \
                len(grids))

    grid = grids[0]
    grid_meta = {'ver':'2.0'}
    grid_cols = []
    grid_rows = []
    json_grid = {
            'meta': grid_meta,
            'cols': grid_cols,
            'rows': grid_rows,
    }

    grid_meta.update(grid.metadata)
    def _col_to_json(c):
        (name, meta) = c
        json_col = dict(meta)
        json_col['name'] = name
        return json_col
    grid_cols.extend(map(_col_to_json, grid.column.items()))
    grid_rows.extend(grid)
    return json_grid
