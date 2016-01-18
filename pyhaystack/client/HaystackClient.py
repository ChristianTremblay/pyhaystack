#!python
# -*- coding: utf-8 -*-
"""
File : HaystackClient.py (2.x)

"""

import logging
import requests
import json
import time
import hszinc
from ..history.HisRecord import HisRecord
#from ..io.read import read
from ..io.zincParser import zincToJson
from ..io.jsonParser import json_decode
from ..io.haystackRead import HReadAllResult
from ..exception import HaystackError

try:
    # Python 3.x case
    from urllib.parse import quote_plus
except ImportError:
    # Python 2.x case
    from urllib import quote_plus

def mk_query(**kwargs):
    '''
    Construct a URI query string from the arguments given.
    '''
    return '&'.join([
        '%s=%s' % (arg, quote_plus(val))
        for arg, val in kwargs.items()
    ])


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
        self._zinc = bool(kwargs.pop('zinc',False))
        self._history = None
        self._history_expiry = 0

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

    def read(self, urlToGet, **kwargs):
        if self._zinc:
            return self.getZinc(urlToGet, **kwargs)
        else:
            return self.getJson(urlToGet, **kwargs)

    def getJson(self, urlToGet, **kwargs):
        """
        Helper for GET request. Retrieve information as json string objects
        urlToGet must include only the request ex. "read?filter=site"
        Queryurl (ex. http://serverIp/haystack) is already known

        Query arguments should be passed as kwargs.
        """
        if not self.isConnected:
            self.authenticate()

        url = self.queryURL + urlToGet
        if bool(kwargs):
            # additional query string
            url += '?' + mk_query(**kwargs)

        kwargs = self._get_kwargs(headers=dict(
            accept='application/json; charset=utf-8'))
        self._log.getChild('http').debug(
                'Submitting JSON GET request for %s, headers: %s',
                url, kwargs.get('headers',{}))

        req = self.s.get(url, **kwargs)
        req.raise_for_status()
        decoded = hszinc.parse(req.json(), mode=hszinc.MODE_JSON)
        if 'err' in decoded.metadata:
            raise HaystackError(decoded.metadata.get('dis', 'Unknown error'),
                                traceback=decoded.metadata.get('traceback',None))
        return decoded

    def getZinc(self, urlToGet, **kwargs):
        """
        Helper for GET request. Retrieve information as default Zinc string
        objects
        """
        if not self.isConnected:
            self.authenticate()

        url = self.queryURL + urlToGet
        if bool(kwargs):
            # additional query string
            url += '?' + mk_query(**kwargs)

        kwargs = self._get_kwargs(headers=dict(
            accept='text/plain; charset=utf-8'))
        self._log.getChild('http').debug(
                'Submitting ZINC GET request for %s, headers: %s',
                url, kwargs.get('headers',{}))
        req = self.s.get(url, **kwargs)
        req.raise_for_status()
        decoded = hszinc.parse(req.text, mode=hszinc.MODE_ZINC)[0]
        if 'err' in decoded.metadata:
            raise HaystackError(decoded.metadata.get('dis', 'Unknown error'),
                                traceback=decoded.metadata.get('traceback',None))
        return decoded

    def _post_request(self, url, content_type, data, headers=None, **kwargs):
        """
        Helper for POST request
        """
        if headers is None:
            headers = {}

        headers['Content-Type'] = content_type
        url = self.queryURL + url
        kwargs = self._get_kwargs(headers=headers, **kwargs)
        self._log.getChild('http').debug(
                'Submitting POST request for %s, headers: %s, data: %r',
                url, kwargs.get('headers',{}), data)
        req = self.s.post(url, data=data, **kwargs)
        req.raise_for_status()
        return req

    def _post_grid(self, url, grid, headers=None, **kwargs):
        """
        Post a grid to the Haystack server.
        """
        if self._zinc:
            content_type = 'application/json'
            data = hszinc.dump(grid, mode=hszinc.MODE_JSON)
        else:
            content_type = 'text/zinc'
            data = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

        return self._post_request(url, content_type, data, headers, **kwargs)

    @property
    def allHistories(self):
        '''
        Return a list of all history items known to the client.
        '''
        self.refreshHisList()
        return self._history.copy()

    def getHistMeta(self, hist_id):
        '''
        Get the metadata for a given historical data point.  Raises KeyError
        if the item does not exist.
        '''
        self.refreshHisList()
        return self._history[hist_id]

    def refreshHisList(self, force_refresh=False):
        """
        This function retrieves every histories in the server and returns a
        list of id
        """
        if (self._history_expiry > time.time()) and (not force_refresh):
            return

        history = {}
        for pt in self.read('read', filter='his'):
            pt_id = pt.pop('id')
            if pt_id.has_value:
                pt['name'] = pt_id.value
            history[pt_id.name] = pt
        self._history = history
        self._history_expiry = time.time() + 300.0  # TODO: make configurable

    def hisAll(self):
        """
        Returns all history names and id
        """
        self.refreshHisList()
        return [
                {'id': his_id, 'name': his_meta.get('name')} \
                        for his_id, his_meta in
                        self._history.items()
        ]

    def readAll(self, filterRequest):
        """
        Returns result of filter request
        """
        # Should add some verification here
        log = self._log.getChild('read_all')
        result = self.read(req, filter=filterRequest)

        if log.isEnabledFor(logging.DEBUG):
            log.debug('Read %d rows:\n%s', '\n'.join([
                '  %s' % each['dis']
                for each in result]))
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
        rng = kwargs.pop('rng',None)
        start = kwargs.pop('start',None)
        end = kwargs.pop('end',None)
        takeall = kwargs.pop('all','')
        # Remaining kwargs...
        if kwargs: raise TypeError('Unknown argument(s) : %s' % kwargs)

        # Build datetimeRange based on start and end
        if (start is not None) and (end is not None):
            if rng is not None:
                raise ValueError('rng and start/end are mutually exclusive')
            datetimeRange = (start, end)
        elif rng is not None:
            datetimeRange = rng
        else:
            raise ValueError('start and end or rng is required')


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

    def hisWrite(self, records):
        '''
        Write one or more records to one or more entities.

        records may be:
        - a list of dicts
        - a single dict (for a single record)

        the dicts take the form:
        - a key named 'ts' with a datetime object
        - IDs and the sample values in key-value pairs.
        '''
        if isinstance(records, dict):
            records = [records]

        # Get a list of all points being written to.
        points = set()
        for r in records:
            points.update(set(r.keys()) - set(['ts']))

        # Get the timezones needed for each point
        tz = dict([
            (point, hszinc.zoneinfo.timezone(self.getHistMeta(point)['tz']))
            for point in points
        ])

        if len(points) == 1:
            # Single point hist-write.
            point_id = list(points)[0]
            tz = tz[point_id]
            grid = hszinc.Grid()
            grid.metadata['id'] = hszinc.Ref(point_id)
            grid.column['ts'] = {}
            grid.column['val'] = {}
            for r in records:
                ts = r['ts']
                value = r[point_id]

                # Localise timestamp
                if ts.tzinfo is None:
                    ts = tz.localize(ts)
                else:
                    ts = ts.astimezone(tz)

                grid.append({'ts': ts, 'val': value})
        else:
            # Multi-point hist-write.
            grid = hszinc.Grid()
            grid.metadata['id'] = hszinc.Ref(point_id)
            grid.column['ts'] = {}
            grid_cols = {}
            for num, point in zip(range(0, len(points)), points):
                col = 'v%d' % num
                grid_cols[point] = col
                grid.column[col] = {'id': hszinc.Ref(point)}

            for r in records:
                ts = r['ts']
                row = {}

                for point, col in grid_cols.items():
                    if 'ts' not in row:
                        # Localise timestamp
                        if ts.tzinfo is None:
                            row['ts'] = tz[point].localize(ts)
                        else:
                            row['ts'] = ts.astimezone(tz[point])
                    row[col] = r.get(point)
                grid.append(row)

        self._post_grid('hisWrite', grid)
