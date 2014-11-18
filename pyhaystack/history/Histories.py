# -*- coding: utf-8 -*-
"""
Created on Tue Nov 18 14:21:49 2014

@author: CTremblay
"""

class Histories():
    """
    This class gathers every histories on the Jace
    """
    def __init__(self, session):
        self._allHistories = []
        self._filteredList = []
        self._his = {'name':'',
                     'id':''}
       
        
        for each in session.getJson("read?filter=his")['rows']:
            self._his['name'] = each['id'].split(' ',1)[1]
            self._his['id'] = each['id'].split(' ',1)[0]
            #self._his['data'] = ''#No data right now
            self._allHistories.append(self._his.copy())
            
    def getListofIdsAndNames(self):
        return self._allHistories

#    def getDataFrameOf(self, hisId, dateTimeRange='today'):
#            return HisRecord(self,hisId,dateTimeRange)
        