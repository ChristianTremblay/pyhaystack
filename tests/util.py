#!python
# -*- coding: utf-8 -*-
"""
Helper functions for test cases in Pyhaystack
"""

# Assume unicode literals as per Python 3
from __future__ import unicode_literals

import hszinc


def grid_meta_cmp(msg, expected, actual):
    errors = []
    for key in set(expected.keys()) | set(expected.keys()):
        if key not in expected:
            errors.append("%s key %s unexpected" % (msg, key))
        elif key not in actual:
            errors.append("%s key %s missing" % (msg, key))
        else:
            ev = expected[key]
            av = actual[key]
            if ev != av:
                errors.append("%s key %s was %r not %r" % (msg, key, av, ev))
    return errors


def grid_col_cmp(expected, actual):
    errors = []
    for col in set(expected.keys()) | set(actual.keys()):
        if col not in expected:
            errors.append("unexpected column %s" % col)
        elif col not in actual:
            errors.append("missing column %s" % col)
        else:
            errors.extend(grid_meta_cmp("column %s" % col, expected[col], actual[col]))
    return errors


def grid_cmp(expected, actual):
    assert isinstance(expected, hszinc.Grid), "expected is not a grid"
    assert isinstance(actual, hszinc.Grid), "actual is not a grid"

    errors = grid_meta_cmp("grid metadata", expected.metadata, actual.metadata)
    errors.extend(grid_col_cmp(expected.column, actual.column))

    for idx in range(0, max(len(expected), len(actual))):
        try:
            erow = expected[idx]
        except IndexError:
            erow = None
        try:
            arow = actual[idx]
        except IndexError:
            arow = None

        if erow is None:
            errors.append("Unexpected row %d: %r" % (idx, arow))
        elif arow is None:
            errors.append("Missing row %d: %r" % (idx, erow))
        else:
            errors.extend(grid_meta_cmp("Row %d" % idx, erow, arow))

    if errors:
        assert False, "Grids do not match:\n- %s" % ("\n- ".join(errors))
