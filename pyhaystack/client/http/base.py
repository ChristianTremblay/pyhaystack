# -*- coding: utf-8 -*-
"""
Base HTTP client handler class.  This wraps a HTTP client library in a
consistent interface to make processing and handling of requests more
convenient and to aid portability of pyhaystack.
"""

# Assume unicode literals as per Python 3
from __future__ import unicode_literals

import shlex
import re

try:
    from urllib.parse import quote_plus
except ImportError:
    from urllib import quote_plus

try:
    from urllib.parse import urljoin
except ImportError:
    from urllib import basejoin as urljoin

from .auth import AuthenticationCredentials


class HTTPClient(object):
    """
    The base HTTP client interface.  This class defines methods for making
    HTTP requests in a unified manner.  The interface presented is an
    asynchronous one, even for synchronous implementations.
    """

    PROTO_RE = re.compile(r"^[a-z]+://")
    CONTENT_TYPE_HDR = b"Content-Type"
    CONTENT_LENGTH_HDR = b"Content-Length"

    def __init__(
        self,
        uri=None,
        params=None,
        headers=None,
        cookies=None,
        auth=None,
        timeout=None,
        proxies=None,
        tls_verify=None,
        tls_cert=None,
        accept_status=None,
        log=None,
        insecure_requests_warning=True,
        requests_session=True,
    ):
        """
        Instantiate a HTTP client instance with some default parameters.
        These parameters are made accessible as properties to be modified at
        will by the caller as needed.

        :param uri:     Base URI for all requests.  If given, this string will
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
        :param log:     If not None, then it's a logging object that will be
                        used for debugging HTTP operations.
        :param requests_session: 
                        Request sessions handles a lot of things
                        inclusding cookies and it is problematic with some
                        implementations like Skyspark. This flag allows to 
                        disable this Session and eliminate cookies round-trip.
        """

        # Stash these defaults for later.  These can be modified at any time
        # by the caller.
        self.uri = uri
        self.params = params
        self.headers = headers
        self.cookies = cookies
        self.auth = auth
        self.timeout = timeout
        self.proxies = proxies
        self.tls_verify = tls_verify
        self.tls_cert = tls_cert
        self.log = log

        if not insecure_requests_warning:
            self.silence_insecured_warnings()
        self.requests_session = requests_session

    def request(
        self,
        method,
        uri,
        callback,
        body=None,
        params=None,
        headers=None,
        cookies=None,
        auth=None,
        timeout=None,
        proxies=None,
        tls_verify=None,
        tls_cert=None,
        exclude_params=None,
        exclude_headers=None,
        exclude_cookies=None,
        exclude_proxies=None,
        accept_status=None,
    ):
        """
        Perform a request with this client.  Most parameters here exist to either
        add to or override the defaults given by the client attributes.  The
        parameters exclude_... serve to allow selective removal of defaults.

        :param method:  The HTTP method to request.
        :param uri:     URL for this request.  If this is a relative URL, it
                        will be relative to the URL given by the 'uri'
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
        :param accept_status:
                        If not None, this gives a list of status codes that
                        will not raise an error, but instead be passed through
                        for the Haystack client to handle.
        """
        # Is this an absolute URL?
        if not self.PROTO_RE.match(uri):
            # Do we have a base URL?
            if self.uri is None:
                raise ValueError("uri must be absolute or base " "set in uri attribute")
            # Prepend our base URL
            uri = urljoin(self.uri, uri)

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

            if self.log is not None:
                self.log.debug(
                    "Merging %r with %r, exclude %s -> %r",
                    given,
                    defaults,
                    exclude,
                    result,
                )
            return result

        # Merge our parameters, headers and cookies together
        params = _merge(params, self.params, exclude_params)
        headers = _merge(headers, self.headers, exclude_headers)
        cookies = _merge(cookies, self.cookies, exclude_cookies)
        proxies = _merge(proxies, self.proxies, exclude_proxies)
        auth = auth or self.auth or None
        timeout = timeout or self.timeout or None

        if not ((auth is None) or isinstance(auth, AuthenticationCredentials)):
            raise TypeError(
                "%s is not a subclass of the "
                "AuthenticationCredentials class." % auth.__class__.__name__
            )

        if tls_verify is None:
            tls_verify = self.tls_verify
            if (tls_verify is None) and uri.startswith("https://"):
                # If we're dealing with a https:// URL, turn on verification
                # by default for user safety.
                tls_verify = True
        tls_cert = tls_cert or self.tls_cert or None

        # Convert parameters to a query string
        query_str = "&".join(
            ["%s=%s" % (key, quote_plus(value)) for key, value in params.items()]
        )

        # Tack query string onto URL
        if query_str:
            uri += "?" + query_str

        # Perform the actual request.
        if self.log is not None:
            self.log.debug(
                "Performing operation %s of %s, headers: %r, " "cookies: %r, body: %r",
                method,
                uri,
                headers,
                cookies,
                body,
            )
        self._request(
            method=method,
            uri=uri,
            callback=callback,
            body=body,
            headers=headers,
            cookies=cookies,
            auth=auth,
            timeout=timeout,
            proxies=proxies,
            tls_verify=tls_verify,
            tls_cert=tls_cert,
            accept_status=accept_status,
        )

    def get(self, uri, callback, **kwargs):
        """
        Convenience function: perform a HTTP GET operation.  Arguments are the
        same as for request.
        """
        kwargs.pop("body", None)
        self.request("GET", uri, callback, **kwargs)

    def post(
        self,
        uri,
        callback,
        body=None,
        body_type=None,
        body_size=None,
        headers=None,
        **kwargs
    ):
        """
        Convenience function: perform a HTTP POST operation.  Arguments are the
        same as for request.

        :param body:        Body data to be posted in this request as a string.
        :param body_type:   Body MIME data type.  This is a convenience for setting
                            the Content-Type header.
        :param body_size:   Length of the body to be sent.  If None, the length
                            is autodetected.  Set to False to avoid this.
        """
        if headers is None:
            headers = {}

        if body is not None:
            if body_size is None:
                body_size = len(body)

            if body_size is not False:
                headers[self.CONTENT_LENGTH_HDR] = str(body_size)

            if body_type is not None:
                headers[self.CONTENT_TYPE_HDR] = body_type

        self.request(
            method="POST",
            uri=uri,
            callback=callback,
            body=body,
            headers=headers,
            **kwargs
        )

    def _request(
        self,
        method,
        uri,
        callback,
        body,
        headers,
        cookies,
        auth,
        timeout,
        proxies,
        tls_verify,
        tls_cert,
        accept_status,
    ):
        """
        Perform a HTTP request using the underlying implementation.  This is
        expected to take the arguments given, perform a query, then return the
        result via a callback.
        """
        raise NotImplementedError("TODO: implement in %s" % self.__class__.__name__)

    def silence_insecured_warnings(self):
        """
        Can be used to disable Insecure Requests Warnings
        in "controlled" environment.
        Use with care.
        """
        if self.log is not None:
            self.log.warning(
                "Disabling insecure requests warnings. Please use with care. Unverified HTTPS requests will be made. Adding Certificate verification is strongly advised."
            )
        try:
            import requests
            from requests.packages.urllib3.exceptions import InsecureRequestWarning

            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        except ImportError:
            raise


class HTTPResponse(object):
    """
    A class that represents the raw response from a HTTP request.
    """

    def __init__(self, status_code, headers, body, cookies=None):
        self.status_code = status_code
        self.headers = CaseInsensitiveDict(headers or {})
        self.body = body
        self.cookies = CaseInsensitiveDict(cookies or {})
        self._content_type = None
        self._content_type_args = None
        self._text = None

    @property
    def content_type(self):
        """
        Return the content type of the body.
        """
        if self._content_type is None:
            self._parse_content_type()
        return self._content_type

    @property
    def content_type_args(self):
        """
        Return the content type arguments of the body.
        """
        if self._content_type_args is None:
            self._parse_content_type()
        return self._content_type_args.copy()

    @property
    def text(self):
        """
        Attempt to decode the raw body into text based on the encoding given.
        """
        if self._text is None:
            body = self.body
            if not hasattr(body, "decode"):
                # It probably is a str/unicode
                return body

            content_encoding = self.content_type_args.get("charset")
            if content_encoding is None:
                self._text = self.body.decode()
            else:
                self._text = self.body.decode(content_encoding)
        return self._text

    def _parse_content_type(self):
        content_type = self.headers["content-type"]

        # Is content encoding shoehorned in there?
        if ";" in content_type:
            (content_type, content_type_args) = content_type.split(";", 1)
            content_type = content_type.strip()
            content_type_args = dict(
                [tuple(kv.split("=", 1)) for kv in shlex.split(content_type_args)]
            )
        else:
            content_type_args = {}
        self._content_type = content_type
        self._content_type_args = content_type_args


class CaseInsensitiveDict(dict):
    """
    A dict object that maps keys in a case-insensitive manner.
    """

    @classmethod
    def _key_to_str(cls, key):
        # Handle bytes
        if isinstance(key, bytes):
            key = key.decode("utf-8")
        return str(key).lower()

    def __init__(self, *args, **kwargs):
        super(CaseInsensitiveDict, self).__init__(*args, **kwargs)
        self._key_map = dict([(self._key_to_str(k), k) for k in self.keys()])

    def __getitem__(self, key, *args, **kwargs):
        try:
            key = self._key_map[self._key_to_str(key)]
        except KeyError:
            pass
        return super(CaseInsensitiveDict, self).__getitem__(key, *args, **kwargs)

    def __setitem__(self, key, *args, **kwargs):
        self._key_map[self._key_to_str(key)] = key
        return super(CaseInsensitiveDict, self).__setitem__(key, *args, **kwargs)

    def __delitem__(self, key, *args, **kwargs):
        self._key_map.pop(str(key).lower(), None)
        return super(CaseInsensitiveDict, self).__delitem__(key, *args, **kwargs)
