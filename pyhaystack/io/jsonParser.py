# -*- coding: utf-8 -*-
"""
JSON Haystack decoder.  This takes the Haystack extensions used in
Project Haystack and decodes the strings into native Python objects.

Quoting http://project-haystack.org/doc/Json#mapping
The following is the mapping between Haystack and JSON types:

Haystack      JSON
--------      ----
Grid          Object
List          Array
Dict          Object
null          null
Bool          Boolean
Marker        "m:" (
Number        "n:<float> [unit]" "n:45.5" "n:73.2 °F" "n:-INF"
Ref           "r:<id> [dis]"  "r:abc-123" "r:abc-123 RTU #3"
Str           "hello" "s:hello"
Date          "d:2014-01-03"
Time          "h:23:59"
DateTime      "t:2015-06-08T15:47:41-04:00 New_York"
Uri           "u:http://project-haystack.org/"
Bin           "b:<mime>" "b:text/plain"
Coord         "c:<lat>,<lng>" "c:37.545,-77.449"

@author: Stuart Longland
"""
import json
import hszinc
from hszinc import zoneinfo
import datetime
import re
import iso8601

# Type regular expressions
MARKER      = 'm:'
NUMBER_RE   = re.compile(r'^n:(\d+(:?\.\d+)?(:?[eE][+\-]?\d+)?)(:? (.*))?$')
REF_RE      = re.compile(r'^r:([a-zA-Z0-9_:\-.~]+)(:? (.*))?$')
STR_RE      = re.compile(r'^s:(.*)$')
DATE_RE     = re.compile(r'^d:(\d{4})-(\d{2})-(\d{2})$')
TIME_RE     = re.compile(r'^h:(\d{2}):(\d{2})(:?:(\d{2}(:?\.\d+)?))$')
DATETIME_RE = re.compile(r'^t:(\d{4}-\d{2}-\d{2}T'\
        r'\d{2}:\d{2}(:?:\d{2}(:?\.\d+)?)'\
        r'(:?[zZ]|[+\-]\d+:?\d*))(:? ([A-Za-z\-_0-9]+))?$')
URI_RE      = re.compile(r'u:(.+)$')
BIN_RE      = re.compile(r'b:(.+)$')
COORD_RE    = re.compile(r'c:(\d+\.?\d*),(\d+\.?\d*)$')

def json_decode(raw_json):
    '''
    Recusively scan the de-serialised JSON tree for objects that correspond to
    standard Haystack types and return the Python equivalents.
    '''
    # Simple cases
    if raw_json is None:
        return None
    elif raw_json == MARKER:
        return hszinc.MARKER
    elif isinstance(raw_json, dict):
        result = {}
        for key, value in raw_json.items():
            result[json_decode(key)] = json_decode(value)
        return result
    elif isinstance(raw_json, list):
        return list(map(json_decode, raw_json))
    elif isinstance(raw_json, tuple):
        return tuple(map(json_decode, raw_json))

    # Is it a number?
    match = NUMBER_RE.match(raw_json)
    if match:
        # We'll get a value and a unit, amongst other tokens.
        matched = match.groups()
        value = float(matched[0])
        if matched[-1] is not None:
            # It's a quantity
            return hszinc.Quantity(value, matched[-1])
        else:
            # It's a raw value
            return value

    # Is it a string?
    match = STR_RE.match(raw_json)
    if match:
        return match.group(1)

    # Is it a reference?
    match = REF_RE.match(raw_json)
    if match:
        matched = match.groups()
        if matched[-1] is not None:
            return hszinc.Ref(matched[0], matched[-1], has_value=True)
        else:
            return hszinc.Ref(matched[0])

    # Is it a date?
    match = DATE_RE.match(raw_json)
    if match:
        (year, month, day) = match.groups()
        return datetime.date(year=int(year), month=int(month), day=int(day))

    # Is it a time?
    match = TIME_RE.match(raw_json)
    if match:
        (hour, minute, second) = match.groups()
        # Convert second to seconds and microseconds
        second = float(second)
        int_second = int(second)
        second -= int_second
        microsecond = second * 1e6
        return datetime.time(hour=int(hour), minute=int(minute),
                second=int_second, microseconds=microsecond)

    # Is it a date/time?
    match = DATETIME_RE.match(raw_json)
    if match:
        matches = match.groups()
        # Parse ISO8601 component
        isodate = iso8601.parse_date(matches[0])
        # Parse timezone
        tzname  = matches[-1]
        if tzname is None:
            return isodate  # No timezone given
        else:
            try:
                tz = zoneinfo.timezone(tzname)
                return isodate.astimezone(tz)
            except:
                return isodate

    # Is it a URI?
    match = URI_RE.match(raw_json)
    if match:
        return hszinc.Uri(match.group(1))

    # Is it a Bin?
    match = BIN_RE.match(raw_json)
    if match:
        return hszinc.Bin(match.group(1))

    # Is it a co-ordinate?
    match = COORD_RE.match(raw_json)
    if match:
        (lat,lng) = match.groups()
        return hszinc.Coord(lat,lng)

    # Maybe it's a bare string?
    return raw_json
