# -*- coding: utf-8 -*-
"""
Created on Tue Nov 18 13:37:36 2014

@author: CTremblay
"""

import json

def isfloat(value):
    """
    Helper function to detect if a value is a float 
    """
    try:
        float(value)
        return True
    except ValueError:
        return False   
        


def prettyprint(jsonData):
    """
    Pretty print json object
    """
    print json.dumps(jsonData, sort_keys=True, indent=4)