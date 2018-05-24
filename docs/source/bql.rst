BQL
=========

[ref: Getting Started with Niagara | docUser.pdf | Niagara documentation]
BQL is one Scheme used to Query in the Niagara Framework. An Ord is made up of 
one or more Queries. A
Query includes a Scheme and a body. The bql Scheme has a body with one of the 
following formats:
 • BQL expression
 • Select projection FROM extent Where predicate
You can create the Ord Qualifier, Select, FROM and Where portions of a Query.

Usage
++++++
Technically, BQL can be used to retrieve any information from a Niagara station.
One really useful usage would be to request data from the alarm database or 
from the audit history.

::

        bql_request = "station:|alarm:/|bql:select timestamp, alarmData.sourceName, \
        normalTime,ackTime,alarmData.timeInAlarm, msgText, user, alarmData.lowLimit, \
        alarmData.highLimit,alarmData.alarmValue, alarmData.notes, sourceState, ackState"
        
        yesterday_alarms = bql_request + ' where timestamp in bqltime.yesterday'

        alarms = session.get_bql(yesterday_alarms).result

The result will be a pandas dataframe.
