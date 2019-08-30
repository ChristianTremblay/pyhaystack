# -*- coding: utf-8 -*-
import json
import re

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

def isBool(value):
    """
    Helper function to detect if a value is boolean
    """
    if value != '':
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
    print('%s' % json.dumps(jsonData, sort_keys=True, indent=4))

def niagara_unescape(s):
    """
    Niagara and nhaystack will spit out ~xy characters
    Those are in fact unicode and can be escaped to be
    easier to read

    "H.Client.Labo~2f222~2dBA~2fPC_D~e9bit_Alim"
    becomes
    "H.Client.Labo/222-BA/PC_Débit_Alim"
    """
    _s = s
    escape = re.compile(r'~(\w\w)')
    for each in escape.finditer(_s):
        _s = re.sub(each[0],chr(int(each[1], base=16)),_s)
    return _s