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
    metaInfo = req[0].split(' ')   
    keys = req[1].split(',')
    grid = req[2:]
        
    result = {}
    rows = []
    cols = []
    meta = []
    
    #Build Meta
    for each in metaInfo:
        if each != '':
            metaDict = {each.split(':')[0].replace('"','') : each.split(':')[1].replace('"','') }
            meta.append(metaDict)
    #Buil cols    
    for each in keys:
        if each != '':
            colsDict = {'name' : each.replace('"','')}
            cols.append(colsDict)
    
    # Building Rows
    for each in grid:
        if each != '':
            values = each.replace('"','').split(',')
            rowsDict = dict(zip(keys, values))
            rows.append(rowsDict)
    
    result['meta'] = meta
    result['cols'] = cols
    result['rows'] = rows
    
    jsondict = json.dumps(result)
    return jsondict