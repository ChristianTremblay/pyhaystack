#!python
# -*- coding: utf-8 -*-
"""
File : HaystackClient.py (2.x)

"""

import requests
import json
from pyhaystack.history.HisRecord import HisRecord
from pyhaystack.history.Histories import Histories
#from pyhaystack.io.read import read
from pyhaystack.io.zincParser import zincToJson
from pyhaystack.io.haystackRead import HReadAllResult

class Connect():
    """
    Abstact class / Make a connection object to haystack server using requests module
    A class must be made for different type of server. See NiagaraAXConnection(HaystackConnection)
    """
    def __init__(self, url, username, password,**kwargs):
        """
        Set local variables
        Open a session object that will be used for connection, with keep-alive feature
            baseURL : http://XX.XX.XX.XX/ - Server URL
            queryURL : ex. for nhaystack = baseURL+haystack = http://XX.XX.XX.XX/haystack
            USERNAME : used for login
            PASSWORD : used for login
            **kwargs :
                zinc = False or True (compatibility for old device like NPM2 that cannot generate Json coding)

            COOKIE : for persistent login
            isConnected : flag to be used for connection related task (don't try if not connected...)
            s : requests.Session() object
            _filteredList : List of histories created by getFilteredHistories
            timezone : timezone from site description
        """
        self.baseURL = url
        self.queryURL = ''
        self.USERNAME = username
        self.PASSWORD = password
        self.COOKIE = ''
        self.isConnected = False
        self.s = requests.Session()
        self._filteredList = []
        self.timezone = 'UTC'
        self._forceZincToJson = kwargs.pop('zinc','False')

        # Headers to pass in each request.
        self._rq_headers = {}

    def _get_headers(self, **kwargs):
        '''
        Get a dict of headers to submit.
        '''
        headers = self._rq_headers.copy()
        headers.update(kwargs)
        return headers

    def authenticate(self):
        """
        This function must be overridden by specific server connection to fit particular needs (urls, other conditions)
        """
        pass

    def read(self,urlToGet):
        if self._forceZincToJson:
            return self.getZinc(urlToGet)
        else:
            return self.getJson(urlToGet)

    def getJson(self,urlToGet):
        """
        Helper for GET request. Retrieve information as json string objects
        urlToGet must include only the request ex. "read?filter=site"
        Queryurl (ex. http://serverIp/haystack) is already known
        """
        if self.isConnected:
            try:
                req = self.s.get(self.queryURL + urlToGet, headers=self._get_headers(accept='application/json; charset=utf-8'))
                return json.loads(req.text)
            except requests.exceptions.RequestException as e:
                print('Request GET error : %s' % e)
        #else:
        #print 'Session not connected to server, cannot make request'
        else:
            print('Session not connected to server, cannot make request')

    def getZinc(self,urlToGet):
        """
        Helper for GET request. Retrieve information as default Zinc string objects
        """
        if self.isConnected:
            try:
                req = self.s.get(self.queryURL + urlToGet, headers=self._get_headers(accept='text/plain; charset=utf-8'))
                return json.loads(zincToJson(req.text))
            except requests.exceptions.RequestException as e:
                print('Request GET error : %s' % e)
        else:
            print('Session not connected to server, cannot make request')

    def postRequest(self,url,headers={'token':''}):
        """
        Helper for POST request
        """
        try:
            req = self.s.post(url, params=headers,auth=(self.USERNAME, self.PASSWORD))
            #print 'Post request response : %s' % req.status_code
            #print 'POST : %s | url : %s | headers : %s | auth : %s' % (req, url, headers,self.USERNAME) Gives a 404 response but a connection ????
        except requests.exceptions.RequestException as e:    # This is the correct syntax
            print('Request POST error : %s' % e)

    def refreshHisList(self):
        """
        This function retrieves every histories in the server and returns a list of id
        """
        print('Retrieving list of histories (trends) in server, please wait...')
        self.allHistories = Histories(self)
        print('Complete... Use hisAll() to check for trends or refreshHisList() to refresh the list')
        print('Try hisRead() to load a bunch of trend matching criterias')

    def hisAll(self):
        """
        Returns all history names and id
        """
        return self.allHistories.getListofIdsAndNames()

    def readAll(self,filterRequest):
        """
        Returns result of filter request
        """
        # Should add some verification here
        req = 'read?filter=' + filterRequest
        result = self.read(req)

        for each in result['rows']:
            print('%s' % each['dis'])
        return HReadAllResult(self,result)

    def hisRead(self,**kwargs):
        """
        This method returns a list of history records
        arguments are :
        ids : a ID or a list of ID
        AND_search : a list of keywords to look for in trend names
        OR_search : a list of keywords to look for in trend names
        rng : haystack range (today,yesterday, last24hours...
        start : string representation of start time ex. '2014-01-01T00:00'
        end : string representation of end time ex. '2014-01-01T00:00'
        """
        self._filteredList = [] # Empty list to be returned
        # Keyword Arguments
        print(kwargs)
        ids = kwargs.pop('id','')
        AND_search = kwargs.pop('AND_search','')
        OR_search = kwargs.pop('OR_search','')
        rng = kwargs.pop('rng','')
        start = kwargs.pop('start','')
        end = kwargs.pop('end','')
        takeall = kwargs.pop('all','')
        # Remaining kwargs...
        if kwargs: raise TypeError('Unknown argument(s) : %s' % kwargs)

        # Build datetimeRange based on start and end
        if start and end:
            datetimeRange = start+','+end
        else:
            datetimeRange = rng


        # Find histories matching ALL keywords in AND_search
        for eachHistory in self.hisAll():
            takeit = False
            # Find histories matching ANY keywords in OR_search
            if (AND_search != '') and all([keywords in eachHistory['name'] for keywords in AND_search]):
                print('AND_search : Adding %s to recordList' % eachHistory['name'])
                takeit = True

            # Find histories matching ANY ID in id list
            elif (OR_search != '') and any([keywords in eachHistory['name'] for keywords in OR_search]):
                print('OR_search : Adding %s to recordList' % eachHistory['name'])
                takeit = True

            elif (ids != '') and any([id in eachHistory['id'] for id in ids]):
                print('ID found : Adding %s to recordList' % eachHistory['name'])
                takeit = True

            elif takeall != '':
                print('Adding %s to recordList' % eachHistory['name'])
                takeit = True

            if takeit:
                self._filteredList.append(HisRecord(self,eachHistory['id'],datetimeRange))


        if self._filteredList == []:
            print('No trends found... sorry !')

        return self._filteredList
