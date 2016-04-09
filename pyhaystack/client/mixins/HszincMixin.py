# -*- coding: utf-8 -*-
"""
Created on Sat Jan 23 20:57:16 2016

@author: CTremblay, sjlongland
"""
from ...exception import HaystackError
import hszinc
import json

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

class HszincMixin(object):
    """
    This class holds every functions related to hszinc that apply to
    HaystackClient
    """
    
    def _get_points_from_grid(self, grid):
        """
        Parse the points returned in the grid and create/update them here
        as required.
        """
        found = {}
        for row in grid:
            point_id = row.get('id',None)
            if point_id is None:
                continue
            point_id = point_id.name

            # Does the point already exist?
            try:
                # It does, refresh its metadata from the row given
                point = self._point[point_id]
                point._load_meta(row)
            except KeyError:
                # Nope, create a new one.
                point = self._POINT_CLASS(self, point_id, row)
                self._point[point_id] = point

            found[point_id] = point
        return found

    def _get_grid(self, url, **kwargs):
        """
        Read a grid via GET from the given URL, optionally with query arguments.
        """
        if not self.isConnected:
            self.authenticate(refreshHisList = False)

        if bool(kwargs):
            # additional query string
            url += '?' + mk_query(**kwargs)
        response = self._get_request(url)
        return self._parse_response(response)

    def _parse_response(self, res):
        """
        Parse the response sent back from the Haystack server.
        """
        #decoded = '' # Referenced before assignment protection
        # content_type we get with nHaystack is Content_type : application/json; charset=UTF-8
        content_type = res.headers['Content-Type']
        if ';' in content_type:
            # Separate encoding from content type
            (content_type, encoding) = content_type.split(';',1)
            content_type = content_type.strip()
            # TODO: do we need to convert to Unicode, of so, how?

        if content_type in ('text/zinc', 'text/plain'):
            decoded = hszinc.parse(res.text, mode=hszinc.MODE_ZINC)[0]
        elif 'application/json' in content_type:
            decoded = hszinc.parse(res.text, mode=hszinc.MODE_JSON)
        else:
            raise NotImplementedError("Don't know how to parse type %s" \
                    % content_type)
        if 'err' in decoded.metadata:
            raise HaystackError(decoded.metadata.get('dis', 'Unknown error'),
                    traceback=decoded.metadata.get('traceback',None))
        return decoded


    def _post_grid(self, url, grid, headers=None, **kwargs):
        """
        Post a grid to the Haystack server.
        """

        if not self.isConnected:
            self.authenticate()

        if self._zinc:
            content_type = 'application/json'
            data = hszinc.dump(grid, mode=hszinc.MODE_JSON)
        else:
            content_type = 'text/zinc'
            data = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

        return self._post_request(url, content_type, data, headers, **kwargs)

    def _post_grid_rq(self, url, grid, headers=None, accept=None, **kwargs):
        """
        Post a request grid to the Haystack server then parse the response.
        """
        if headers is None:
            headers = {}

        if accept is None:
            if self._zinc:
                accept = 'text/zinc'
            else:
                accept = 'application/json'

        headers['Accept'] = accept

        return self._parse_response(self._post_grid(
            url, grid, headers=headers, **kwargs))

    def _exec(self, url, data, headers=None, **kwargs):
        """
        Execute an "exec" API call.
        """
        return self._parse_response(self._post_request(
            url, 'text/plain', data, headers=headers, **kwargs))

    def commit(self, diff):
        """
        Implements skyspark commit. It accepts a Json and returns the server responce.
        :param diff: a Json of the following type:
        {
            "meta":{"ver":"haystack version","commit":"add/update/remove"},
            "cols":[{"name":"col1 name"},{"name":"col2 name"}]
            "rows":[{"col1 name":"col1 val",{"col2 name":"col2 val"}]
        }
        The json needs to have an id. And in case of update or remove, a mod value which is the time of last change.
        :return: returns the servers response as a Json.

        Don't ask.
        """
        return self.s.post(self.queryURL+"commit", data=json.dumps(diff), headers={'accept': 'application/json; charset=utf-8', 'content-type':'application/json'})

    def makeZinc(self,data):
        """
        Not sure if needed. Will convert json to zinc
        :param data:
        :return:
        """
        pass
