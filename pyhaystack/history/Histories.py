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

        for each in session.read("read?filter=his")['rows']:
            try:
                self._his['id'] = each['id'].name
                self._his['name'] = each['id'].value
            except AttributeError:
                self._his['name'] = each['id'].split(' ',1)[1]
                self._his['id'] = each['id'].split(' ',1)[0]
            self._allHistories.append(self._his.copy())

    def getListofIdsAndNames(self):
        return self._allHistories
