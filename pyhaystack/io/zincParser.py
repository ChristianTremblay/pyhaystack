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


def zincToJson(req):
    req = req.split('\n')
    
    keys = req[1].split(',')
    result = {}
    rows = []
    
    for each in req[2:]:
        if each != '':
            values = each.replace('"','').split(',')
            adict = dict(zip(keys, values))
            rows.append(adict)
    
    result['rows'] = rows
    
    jsondict = json.dumps(result)
    return jsondict