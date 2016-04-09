# -*- coding: utf-8 -*-
"""
Created on Sat Jan 23 20:57:16 2016

@author: CTremblay, sjlongland
"""
import time
from functools import wraps

class DisconnectedException(Exception):
    """
    If header returned is something like 'text/html', session is probably
    disconnected.
    """
    pass

def retry(ExceptionToCheck, tries=4, delay=1, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param ExceptionToCheck: the exception to check. may be a tuple of
        exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """
    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as error:
                    msg = "%s, Retrying in %d seconds..." % (str(error), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry
  
class RequestsMixin(object):
    """
    This class holds every functions related to requests that apply to
    HaystackClient
    """
    
    @retry(DisconnectedException)
    def _get_request(self, url, accept=None, headers=None, **kwargs):
        """
        Helper for GET request
        """
        if not self.isConnected:
            self.authenticate(refreshHisList = False)
        
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
        # Detect if disconnected
        if 'text/html' in req.headers['content-type']:
            self.isConnected = False
            raise DisconnectedException('Session disconnected')
            
        return req

    @retry(DisconnectedException)
    def _post_request(self, url, content_type, data, headers=None, **kwargs):
        """
        Helper for POST request
        """
        if not self.isConnected:
            self.authenticate(refreshHisList = False)        
        
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
        # Detect disconnection
        if 'text/html' in req.headers:
            self.isConnected = False
            raise DisconnectedException('Session disconnected')
        return req
