# -*- coding: utf-8 -*-
import json


def isfloat(value):
    """
    Helper function to detect if a value is a float
    """
    if value != "":
        try:
            float(value)
            return True
        except ValueError:
            return False
    else:
        return False


def isBool(value):
    """
    Helper function to detect if a value is boolean
    """
    if value != "":
        if isinstance(value, bool):
            return True
        else:
            return False
    else:
        return False


def prettyprint(jsonData):
    """
    Pretty print json object
    """
    print("%s" % json.dumps(jsonData, sort_keys=True, indent=4))
