# -*- coding: utf-8 -*-
"""
Created on Tue Nov 18 13:40:53 2014
HisRecord must be seen as the representation of one historical trend to be analysed by pandas

@author: CTremblay
"""
import re,datetime
import numpy as np
import pyhaystack.util.tools as tools
import pandas as pd
from pandas import Series

class HisRecord():
    """
    This class is a single record
    - hisId is the haystack Id of the trend
    - data is created as DataFrame to be used directly in Pandas
    """
    def __init__(self,session,hisId,dateTimeRange='today'):
        """
        GET data from server and fill this object with historical info
        """
        # Grab logger child from session
        self._log = session._log.getChild('hisRecord.%s' % hisId)

        self.hisId = hisId
        self.name = self.getHisNameFromId(session,self.hisId)

        result = session.read('hisRead?id=%s&range=%s' % \
                        (self.hisId, dateTimeRange))
        # Convert the list of {ts: foo, val: bar} dicts to a pair of
        # lists.
        if bool(result['rows']):
            (index, values) = zip(*map(lambda row : (row['ts'], row['val']), \
                    result['rows']))
        else:
            # No data
            (index, values) = ([], [])

        try:
            #Declare Series and localize using Site Timezone
            self.data = Series(values,index=index).tz_localize(session.timezone)
            #Renaming index so the name will be part of the serie
            self.data = self.data.reindex(self.data.index.rename([self.name]))
        except:
            log.error('%s is an Unknown history type', self.hisId)
            raise

    def getHisNameFromId(self,session,pointId):
        """
        Retrieve name from id of an history
        """
        for each in session.read("read?filter=his")['rows']:
            try:
                if each['id'].name == pointId:
                    return each['id'].value
            except AttributeError:
                if each['id'].split(' ',1)[0] == pointId:
                    return (each['id'].split(' ',1)[1])
        return 'Id Not found'

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


