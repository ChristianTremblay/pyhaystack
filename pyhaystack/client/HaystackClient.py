#!python
# -*- coding: utf-8 -*-
"""
File : HaystackClient.py (2.x)

"""

import logging
import requests
import json
from pyhaystack.history.HisRecord import HisRecord
from pyhaystack.history.Histories import Histories
#from pyhaystack.io.read import read
from pyhaystack.io.zincParser import zincToJson
from ..io.jsonParser import json_decode
from pyhaystack.io.haystackRead import HReadAllResult

class Connect():
    """
    Abstact class / Make a connection object to haystack server using requests module
    A class must be made for different type of server. See NiagaraAXConnection(HaystackConnection)
    """
    def __init__(self, url, username, password, **kwargs):
        """
        Set local variables
        Open a session object that will be used for connection, with keep-alive feature
            baseURL : http://XX.XX.XX.XX/ - Server URL
            queryURL : ex. for nhaystack = baseURL+haystack = http://XX.XX.XX.XX/haystack
            USERNAME : used for login
            PASSWORD : used for login
            **kwargs :
                zinc = False or True (compatibility for old device like NPM2 that cannot generate Json coding)
                log = logging.Logger instance to use when emitting messages.

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
        self._forceZincToJson = bool(kwargs.pop('zinc',False))

        log = kwargs.pop('log', None)
        if log is None:
            log = logging.getLogger('pyhaystack.client')
        self._log = log

        # Headers to pass in each request.
        self._rq_headers = {}

        # Keyword arguments to pass to each request.
        self._rq_kwargs = {}

    def _get_headers(self, **kwargs):
        '''
        Get a dict of headers to submit.
        '''
        headers = self._rq_headers.copy()
        headers.update(kwargs)
        return headers

    def _get_kwargs(self, **kwargs):
        '''
        Get a dict of kwargs to submit.
        '''
        headers = kwargs.pop('headers',{})
        kwargs = self._rq_kwargs.copy()
        kwargs.update(kwargs)
        kwargs['headers'] = self._get_headers(**headers)
        return kwargs

    def authenticate(self):
        """
        This function must be overridden by specific server connection to fit particular needs (urls, other conditions)
        """
        pass

    def read(self, urlToGet):
        if self._forceZincToJson:
            return self.getZinc(urlToGet)
        else:
            return self.getJson(urlToGet)

    def getJson(self, urlToGet):
        """
        Helper for GET request. Retrieve information as json string objects
        urlToGet must include only the request ex. "read?filter=site"
        Queryurl (ex. http://serverIp/haystack) is already known
        """
        if not self.isConnected:
            self.authenticate()

        url = self.queryURL + urlToGet
        kwargs = self._get_kwargs(headers=dict(
            accept='application/json; charset=utf-8'))
        log.getChild('http', 'Submitting JSON GET request for %s, headers: %s',
                url, headers)

        req = self.s.get(url, **kwargs)
        req.raise_for_status()
        return json_decode(req.json())

    def getZinc(self, urlToGet):
        """
        Helper for GET request. Retrieve information as default Zinc string
        objects
        """
        if not self.isConnected:
            self.authenticate()

        url = self.queryURL + urlToGet
        kwargs = self._get_kwargs(headers=dict(
            accept='text/plain; charset=utf-8'))
        log.getChild('http', 'Submitting ZINC GET request for %s, headers: %s',
                url, headers)
        req = self.s.get(url, **kwargs)
        req.raise_for_status()
        return zincToJson(req.text)

    def postRequest(self, url, headers=None):
        """
        Helper for POST request
        """
        if headers is None:
            headers = {'token': ''}

        req = self.s.post(url, **self._get_kwargs(headers=headers))
        req.raise_for_status()
        return req

    def refreshHisList(self):
        """
        This function retrieves every histories in the server and returns a
        list of id
        """
        self.allHistories = Histories(self)

    def hisAll(self):
        """
        Returns all history names and id
        """
        return self.allHistories.getListofIdsAndNames()

    def readAll(self, filterRequest):
        """
        Returns result of filter request
        """
        # Should add some verification here
        log = self._log.getChild('read_all')
        req = 'read?filter=' + filterRequest
        result = self.read(req)

        if log.isEnabledFor(logging.DEBUG):
            log.debug('Read %d rows:\n%s', '\n'.join([
                '  %s' % each['dis']
                for each in result['rows']]))
        return HReadAllResult(self, result)

    def hisRead(self, **kwargs):
        """
        This method returns a list of history records
        arguments are :
        ids : a ID or a list of ID
        AND_search : a list of keywords to look for in trend names
        OR_search : a list of keywords to look for in trend names
        rng : haystack range (today, yesterday, last24hours...
        start : string representation of start time ex. '2014-01-01T00:00'
        end : string representation of end time ex. '2014-01-01T00:00'
        """
        self._filteredList = [] # Empty list to be returned
        log = self._log.getChild('his_read')
        # Keyword Arguments
        log.debug('Keywords: %s', kwargs)
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
                log.debug('AND_search : Adding %s to recordList',
                    eachHistory['name'])
                takeit = True

            # Find histories matching ANY ID in id list
            elif (OR_search != '') and any([keywords in eachHistory['name'] for keywords in OR_search]):
                log.debug('OR_search : Adding %s to recordList',
                    eachHistory['name'])
                takeit = True

            elif (ids != '') and any([id in eachHistory['id'] for id in ids]):
                log.debug('ID found : Adding %s to recordList',
                        eachHistory['name'])
                takeit = True

            elif takeall != '':
                log.debug('Adding %s to recordList', eachHistory['name'])
                takeit = True

            if takeit:
                self._filteredList.append(HisRecord(self, eachHistory['id'],datetimeRange))


        log.debug('%d trends found', len(self._filteredList))
        return self._filteredList
