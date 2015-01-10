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
        self.hisId = hisId
        self.name = self.getHisNameFromId(session,self.hisId)
        index = []
        values = []

        for eachRows in session.read('hisRead?id='+self.hisId+'&range='+dateTimeRange)['rows']:
            index.append(pd.Timestamp(pd.to_datetime(datetime.datetime(*map(int, re.split('[^\d]', eachRows['ts'].split(' ')[0])[:-2])))))
            #This will allow conversion of Enum value to float so Pandas will work            
            
            
            if (eachRows['val'] == 'F'):
                values.append(False)
            elif (eachRows['val'] == 'T'):
                values.append(True)
            # regex coding here to extract float value when units are part of value (ex. 21.8381°C)
            elif tools.isfloat(re.findall(r"[-+]?\d*\.*\d+", eachRows['val'])[0]):
                values.append(float(re.findall(r"[-+]?\d*\.*\d+", eachRows['val'])[0]))    
            else:
                values.append(eachRows['val'])
        
        try:
            #Declare Series and localize using Site Timezone
            self.data = Series(values,index=index).tz_localize(session.timezone)
            #Renaming index so the name will be part of the serie
            self.data = self.data.reindex(self.data.index.rename([self.name]))
        except Exception:
            print '%s is an Unknown history type' % self.hisId 
    
    def getHisNameFromId(self,session,id):
        """
        Retrieve name from id of an history
        """
        for each in session.read("read?filter=his")['rows']:
            if each['id'].split(' ',1)[0] == id:
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
    
    
