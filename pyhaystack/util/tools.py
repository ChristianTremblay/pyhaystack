# -*- coding: utf-8 -*-
"""
Tools

@author: CTremblay
"""

import json

def isfloat(value):
    """
    Helper function to detect if a value is a float
    """
    if value != '':
        try:
            float(value)
            return True
        except ValueError:
            return False
    else:
        return False



def prettyprint(jsonData):
    """
    Pretty print json object
    """
    print('%s' % json.dumps(jsonData, sort_keys=True, indent=4))