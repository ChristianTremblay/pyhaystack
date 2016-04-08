# -*- coding: utf-8 -*-
"""
Base HTTP client handler class.  This wraps a HTTP client library in a
consistent interface to make processing and handling of requests more
convenient and to aid portability of pyhaystack.
"""

import re
import urllib


class HTTPClient(object):
    """
    The base HTTP client interface.  This class defines methods for making
    HTTP requests in a unified manner.  The interface presented is an
    asynchronous one, even for synchronous implementations.
    """

    PROTO_RE    = re.compile(r'^[a-z]+://')

    def __init__(self, url=None, params=None, headers=None, cookies=None,
            auth=None, timeout=None, proxies=None, tls_verify=None,
            tls_cert=None):
        """
        Instantiate a HTTP client instance with some default parameters.
        These parameters are made accessible as properties to be modified at
        will by the caller as needed.

        :param url:     Base URL for all requests.  If given, this string will
                        be pre-pended to all requests passed through this
                        client.
        :param params:  A dictionary of key-value pairs to be passed as URI
                        query parameters.
        :param headers: A dictionary of key-value pairs to be passed as HTTP
                        headers.
        :param cookies: A dictionary of key-value pairs to be passed as cookies.
        :param auth:    An instance of a HttpAuth object.
        :param timeout: An integer or float giving the default maximum time
                        duration for requests before timing out.
        :param proxies: A dictionary mapping the hostname and protocol to a
                        proxy server URI.
        :param tls_verify:
                        For TLS servers, this determines whether the server
                        is validated or not.  It should be the path to the
                        CA certificate file for this server, or alternatively
                        can be set to 'True' to verify against CAs known to
                        the client. (e.g. OS certificate store)
        :param tls_cert:
                        For TLS servers, this specifies the certificate used
                        by the client to authenticate itself with the server.
        """

        # Stash these defaults for later.  These can be modified at any time
        # by the caller.
        self.url = url
        self.params = params
        self.headers = headers
        self.cookies = cookies
        self.auth = auth
        self.timeout = timeout
        self.proxies = proxies
        self.tls_verify = tls_verify
        self.tls_cert = tls_cert

    def request(self, method, url, callback, body=None, params=None,
            headers=None, cookies=None, auth=None, timeout=None, proxies=None,
            tls_verify=None, tls_cert=None, exclude_params=None,
            exclude_headers=None, exclude_cookies=None, exclude_proxies=None):
        """
        Perform a request with this client.  Most parameters here exist to either
        add to or override the defaults given by the client attributes.  The
        parameters exclude_... serve to allow selective removal of defaults.

        :param method:  The HTTP method to request.
        :param url:     URL for this request.  If this is a relative URL, it
                        will be relative to the URL given by the 'url'
                        attribute.
        :param callback:
                        A callback function that will be presented with the
                        result of this request.
        :param body:    An optional body for the request.
        :param params:  A dictionary of key-value pairs to be passed as URI
                        query parameters.
        :param headers: A dictionary of key-value pairs to be passed as HTTP
                        headers.
        :param cookies: A dictionary of key-value pairs to be passed as cookies.
        :param auth:    An instance of a HttpAuth object.
        :param timeout: An integer or float giving the default maximum time
                        duration for requests before timing out.
        :param proxies: A dictionary mapping the hostname and protocol to a
                        proxy server URI.
        :param tls_verify:
                        For TLS servers, this determines whether the server
                        is validated or not.  It should be the path to the
                        CA certificate file for this server, or alternatively
                        can be set to 'True' to verify against CAs known to
                        the client. (e.g. OS certificate store)
        :param tls_cert:
                        For TLS servers, this specifies the certificate used
                        by the client to authenticate itself with the server.
        :param exclude_params:
                        If True, exclude all default parameters and use only
                        the parameters given.  Otherwise, this is an iterable
                        of parameter names to be excluded.
        :param exclude_headers:
                        If True, exclude all default headers and use only
                        the headers given.  Otherwise, this is an iterable
                        of header names to be excluded.
        :param exclude_cookies:
                        If True, exclude all default cookies and use only
                        the cookies given.  Otherwise, this is an iterable
                        of cookie names to be excluded.
        :param exclude_proxies:
                        If True, exclude all default proxies and use only
                        the proxies given.  Otherwise, this is an iterable
                        of proxy names to be excluded.
        """
        # Is this an absolute URL?
        if not self.PROTO_RE.match(url):
            # Do we have a base URL?
            if self.url is None:
                raise ValueError('url must be absolute or base '\
                        'set in url attribute')
            # Prepend our base URL
            url = urllib.basejoin(self.url, url)

        def _merge(given, defaults, exclude):
            if exclude is True:
                result = {}
            else:
                result = (defaults or {}).copy()
                if exclude is not None:
                    for param in exclude:
                        result.pop(param, None)

            if given is not None:
                result.update(given)
            return result

        # Merge our parameters, headers and cookies together
        params = _merge(params, self.params, exclude_params)
        headers = _merge(headers, self.headers, exclude_headers)
        cookies = _merge(cookies, self.cookies, exclude_cookies)
        proxies = _merge(proxies, self.proxies, exclude_proxies)
        auth = auth or self.auth or None
        timeout = timeout or self.timeout or None
        if tls_verify is None:
            tls_verify = self.tls_verify
            if (tls_verify is None) and url.startswith('https://'):
                # If we're dealing with a https:// URL, turn on verification
                # by default for user safety.
                tls_verify = True
        tls_cert = tls_cert or self.tls_cert or None

        # Convert parameters to a query string
        query_str = u'&'.join([
            '%s=%s' % (key, urllib.quote_plus(value))
            for key, value in params.items()
        ])

        # Tack query string onto URL
        if query_str:
            url += u'?' + query_str

        # Perform the actual request.
        self._request(method, url, callback, body,
                headers, cookies, auth, timeout, proxies,
                tls_verify, tls_cert)

    def get(self, url, callback, **kwargs):
        """
        Convenience function: perform a HTTP GET operation.  Arguments are the
        same as for request.
        """
        kwargs.pop('body',None)
        self.request('GET', url, callback, **kwargs)

    def post(self, url, callback, body, body_type=None, body_size=None,
            headers=None, **kwargs):
        """
        Convenience function: perform a HTTP POST operation.  Arguments are the
        same as for request.

        :param body:        Body data to be posted in this request as a string.
        :param body_type:   Body MIME data type.  This is a convenience for setting
                            the Content-Type header.
        :param body_size:   Length of the body to be sent.  If None, the length
                            is autodetected.  Set to False to avoid this.
        """
        if body_size is None:
            body_size = len(body)

        if headers is None:
            headers = {}

        if body_size is not False:
            headers['Content-Length'] = body_size

        if body_type is not None:
            headers['Content-Type'] = body_type

        self.request('POST', url, callback, body=body,
                headers=headers, **kwargs)

    def _request(self, method, url, callback, body,
            headers, cookies, auth, timeout, proxies,
            tls_verify, tls_cert):
        """
        Perform a HTTP request using the underlying implementation.  This is
        expected to take the arguments given, perform a query, then return the
        result via a callback.
        """
        raise NotImplementedError('TODO: implement in %s' \
                % self.__class__.__name__)


class HTTPBaseError(IOError):
    """
    Error class to represent a HTTP errors.
    """
    pass


class HTTPConnectionError(HTTPBaseError):
    """
    Error class to represent a failed attempt to connect to a host.
    """
    pass


class HTTPTimeoutError(HTTPConnectionError):
    """
    Error class to represent that a request timed out.
    """
    pass


class HTTPRedirectError(HTTPBaseError):
    """
    Error class to represent that the server's redirections are looping.
    """
    pass


class HTTPStatusError(HTTPBaseError):
    """
    Error class to represent a returned failed status from the host.
    """
    def __init__(self, message, status, headers=None):
        self.headers = headers
        self.status = status
        super(HTTPStatusError, self).__init__(message, status)


class AuthenticationCredentials(object):
    """
    A base class to represent authentication credentials.
    """
    pass


class UserPasswordAuthenticationCredentials(AuthenticationCredentials):
    """
    A base class that represents username/password type authentication.
    """
    def __init__(self, username, password):
        self.username = username
        self.password = password


class BasicAuthenticationCredentials(UserPasswordAuthenticationCredentials):
    """
    A class that represents Basic authentication.
    """
    pass


class DigestAuthenticationCredentials(UserPasswordAuthenticationCredentials):
    """
    A class that represents Digest authentication.
    """
    pass
