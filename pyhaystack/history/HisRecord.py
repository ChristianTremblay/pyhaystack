# -*- coding: utf-8 -*-
"""
Created on Tue Nov 18 13:40:53 2014
HisRecord must be seen as the representation of one historical trend to be analysed by pandas

@author: CTremblay
"""
import datetime
import numpy as np
import pandas as pd
from pandas import Series
from hszinc import zoneinfo, Quantity

class HisRecord():
    """
    This class is a single record
    - hisId is the haystack Id of the trend
    - data is created as DataFrame to be used directly in Pandas
    """
    def __init__(self, session, hisId, dateTimeRange='today'):
        """
        GET data from server and fill this object with historical info
        """
        # Grab logger child from session
        self._log = session._log.getChild('hisRecord.%s' % hisId)

        # Grab metadata
        self._meta      = session.getHistMeta(hisId)
        self.tz_name    = self._meta['tz']
        self.tz         = zoneinfo.timezone(self.tz_name)

        # Is dateTimeRange a tuple object?
        if isinstance(dateTimeRange, tuple):
            (dtStart, dtEnd) = dateTimeRange
            # Convert these to native time
            def _to_native(dt):
                self._log.debug('Converting %s to native time', dt)
                if isinstance(dt, datetime.datetime):
                    if dt.tzinfo is None:
                        # Assume time is already local
                        self._log.debug('Localise to timezone %s', self.tz_name)
                        dt = self.tz.localize(dt)
                    else:
                        self._log.debug('Convert to timezone %s', self.tz_name)
                        dt = dt.astimezone(self.tz)

                    return '%s %s' % (dt.isoformat(), self.tz_name)
                elif isinstance(dt, datetime.date):
                    return dt.isoformat()
                else:
                    return dt
            dateTimeRange = '%s,%s' % (_to_native(dtStart), _to_native(dtEnd))

        self.hisId = hisId
        self.name = self._meta.get('name')

        use_eval = hasattr(session, '_eval')
        if use_eval:
            result = session._eval(\
                    'readById(%(hisId)s).hisRead(%(dtRange)s)' \
                    % {
                        'hisId': self.hisId,
                        'dtRange': dateTimeRange.replace(',','..'),
                    })
            val_field = 'v0'
        else:
            result = session._get_grid('hisRead', id='@%s' % self.hisId,
                    range=dateTimeRange)
            val_field = 'val'

        self._log.debug('Received result set: %s', result)
        # Convert the list of {ts: foo, val: bar} dicts to a pair of
        # lists.
        if bool(result):
            strip_unit = lambda v : v.value if isinstance(v, Quantity) else v
            (index, values) = zip(*map(lambda row : \
                            (row['ts'], strip_unit(row[val_field])), result))
        else:
            # No data
            (index, values) = ([], [])

        try:
            #Declare Series converted to local time for session
            self.data = Series(values,index=index).tz_convert(session.timezone)
            #Renaming index so the name will be part of the serie
            self.data = self.data.reindex(self.data.index.rename([self.name]))
        except:
            self._log.error('%s is an Unknown history type', self.hisId)
            raise

    def plot(self):
        """
        Draw a graph of the DataFrame
        """
        self.data.plot()

    def breakdownPlot(self, startTime = '08:00', endTime = '17:00', bins=np.array([0,0.5,1,18.0,18.5,19.0,19.5,20.0,20.5,21.0,21.5,22.0,22.5,23.0, 23.5, 24.0, 24.5,25.0])):
        """
        By default, creates a breakdown plot of temperature distribution between 18 and 25
        bins (distribution) can be past as argument
        By default, takes values between 8:00 and 17:00
        startTime = string representation of time (ex. '08:00')
        endtime = string representation of time (ex. '17:00')
        bin = np.array representing distribution
        """
        x = self.data.between_time(startTime,endTime)
        barplot = pd.cut(x.dropna(),bins)
        x.groupby(barplot).size().plot(kind='bar')
        #self.data.groupby(barplot).size()

    def simpleStats(self):
        """
        Shortcut for describe() pandas version
        """
        return self.data.describe()

    def __str__(self):
        return 'History Record of %s' % self.name

    def __repr__(self):
        return 'pyhaystack History Record of %s' % self.name
