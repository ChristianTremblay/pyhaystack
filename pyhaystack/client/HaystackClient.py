#!python
# -*- coding: utf-8 -*-
"""
File : HaystackClient.py (2.x)

"""

import logging
import requests
import hszinc
import weakref

from .mixins.RequestsMixin import RequestsMixin
from .mixins.HszincMixin import HszincMixin
from .mixins.HistoriesMixin import HistoriesMixin
from ..io.haystackPoint import HaystackPoint

from ..io.haystackRead import HReadAllResult


class Connect(RequestsMixin, HszincMixin, HistoriesMixin):
    """
    Abstact class / Make a connection object to haystack server using requests module
    A class must be made for different type of server. See NiagaraAXConnection(HaystackConnection)
    """

    # Class used for instantiating Haystack data points.
    _POINT_CLASS = HaystackPoint

    def __init__(self, url, username, password, proj = None, **kwargs):
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
        self.PROJECT = proj
        self.COOKIE = ''
        self.isConnected = False
        self.s = requests.Session()
        self._filteredList = []
        self.timezone = 'UTC'
        self._zinc = bool(kwargs.pop('zinc',True))
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

        # Existing point objects
        self._point = weakref.WeakValueDictionary()

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
        raise NotImplementedError()


    @property
    def histories(self):
        '''
        Return a list of all history items known to the client.
        '''
        self.refreshHisList()
        return self._history.copy()

    def read_all(self, filterRequest):
        """
        Returns result of filter request
        :rtype : pyhaystack.io.haystackRead.HReadAllResult
        """
        # Should add some verification here
        log = self._log.getChild('read_all')
        result = self._get_grid('read', filter=filterRequest)

        if log.isEnabledFor(logging.DEBUG):
            log.debug('Read %d rows:\n%s', '\n'.join([
                '  %s' % each['dis']
                for each in result]))
        return HReadAllResult(self, result)


    # Point access

    def find_points(self, filter):
        """
        Find points that match a given filter string.  The filter string
        syntax is given at http://project-haystack.org/doc/Filters.

        A dict of matching points is returned with the IDs as keys.
        """
        # TODO: make an AST abstraction for this filter format.
        return self._get_points_from_grid(self._get_grid('read',
            filter=str(filter)))


    def __getitem__(self, point_ids):
        """
        Get a specific named point or list of points.

        If a single point is requested, the return type is that point, or None
        if not found.

        If a list is given, a dict is returned with the located IDs as keys.
        """
        log = self._log.getChild('getitem')
        multi = isinstance(point_ids, list)
        if not multi:
            log.debug('Retrieving single point %s', point_ids)
            point_ids = [point_ids]
        elif not bool(point_ids):
            log.debug('No points to retrieve')
            return {}

        # Locate items that already exist.
        found = {}
        for point_id in point_ids:
            try:
                point = self._point[point_id]
            except KeyError:
                # It doesn't exist.
                log.debug('Not yet retrieved point %s', point_id)
                continue

            # Is the point due for refresh?
            if point._refresh_due:
                # Pretend it doesn't exist.
                log.debug('Stale point %s', point_id)
                continue

            log.debug('Existing point %s', point_id)
            found[point_id] = point

        # Get a list of points that need fetching
        to_fetch = filter(lambda pid : pid not in found, point_ids)
        log.debug('Need to retrieve points %s', to_fetch)

        if bool(to_fetch):
            if len(to_fetch) > 1:
                # Make a request grid and POST it
                grid = hszinc.Grid()
                grid.column['id'] = {}
                grid.extend([{'id': hszinc.Ref(point_id)}
                            for point_id in to_fetch])
                res = self._post_grid_rq('read', grid)
            else:
                # Make a GET request
                res = self._get_grid('read',
                        id=hszinc.dump_scalar(hszinc.Ref(to_fetch[0])))

            found.update(self._get_points_from_grid(res))

        log.debug('Retrieved %s', list(found.keys()))
        if not multi:
            return found.get(point_ids[0])
        else:
            return found
            
    def disconnext(self):
        """
        Used to disconnect from server
        """
        raise NotImplementedError('Must be overridden')


