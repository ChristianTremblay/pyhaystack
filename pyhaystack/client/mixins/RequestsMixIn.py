# -*- coding: utf-8 -*-
"""
Created on Sat Jan 23 20:57:16 2016

@author: CTremblay, sjlongland
"""

class RequestsMixIn(object):
    """
    This class holds every functions related to requests that apply to
    HaystackClient
    """
    
    def _get_request(self, url, accept=None, headers=None, **kwargs):
        """
        Helper for GET request
        """
        if headers is None:
            headers = {}

        if accept is None:
            if self._zinc:
                accept = 'text/zinc'
            else:
                accept = 'application/json'

        headers['Accept'] = accept
        kwargs = self._get_kwargs(headers=headers, **kwargs)
        url = self.queryURL + url
        self._log.getChild('http').debug(
                'Submitting %s GET request for %s, headers: %s',
                accept, url, kwargs.get('headers',{}))
        req = self.s.get(url, **kwargs)
        req.raise_for_status()
        return req

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
