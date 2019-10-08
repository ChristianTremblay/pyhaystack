# -*- coding: utf-8 -*-
"""
Asynchronous Dummy HTTP client.
"""

from .base import HTTPClient, HTTPResponse
from .auth import BasicAuthenticationCredentials, DigestAuthenticationCredentials
from .exceptions import (
    HTTPConnectionError,
    HTTPTimeoutError,
    HTTPRedirectError,
    HTTPStatusError,
    HTTPBaseError,
)

from ...util.asyncexc import AsynchronousException


class DummyHttpServer(object):
    """
    A Dummy HTTP server.  This class basically provides a controller that
    allows a test HTTP client system to run tests against the library by
    pulling puppet strings on the mock HTTP server.  To use:

    http_server = DummyHttpServer()
    # …
    session = HaystackSessionSubclass(…,
        http_client=DummyHttpClient, http_args={'server': http_server})
    """

    def __init__(self):
        self._requests = {}
        self._rq_order = []
        self._next_id = 0

    def submit_request(
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
        Submit a request.
        """
        rq_id = self._next_id
        self._next_id += 1

        rq = DummyHttpClientRequest(
            rq_id,
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
        )
        self._requests[rq_id] = rq
        self._rq_order.append(rq_id)

    def next_request(self):
        """
        Pop the next request off the queue.
        """
        rq_id = self._rq_order.pop(0)
        return self._requests.pop(rq_id)

    def requests(self):
        """
        Return the number of pending requests.
        """
        return len(self._rq_order)

    def next_requests(self, count=None):
        """
        Pop the next 'count' requests off the queue, or all requests if
        count is not given.
        """
        if count is None:
            count = self.requests()

        while count > 0:
            try:
                rq = self.next_request()
            except IndexError:
                return
            yield rq


class DummyHttpClient(HTTPClient):
    def __init__(self, server, **kwargs):
        super(DummyHttpClient, self).__init__(**kwargs)
        self._server = server

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
        self._server.submit_request(
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
        )


class DummyHttpClientRequest(object):
    """
    A dummy HTTP request.  This class represents a single request being
    made by the client to our dummy HTTP server.  The test suite may then
    inspect all aspects of the request and then submit the expected
    response to the waiting client.
    """

    def __init__(
        self,
        rq_id,
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
        Collect all the parameters supplied in the request.
        """
        self._rq_id = rq_id
        self._method = method
        self._uri = uri
        self._callback = callback
        self._body = body
        self._headers = headers.copy()
        self._cookies = (cookies or {}).copy()
        self._auth = auth
        self._timeout = timeout
        self._proxies = (proxies or {}).copy()
        self._tls_verify = tls_verify
        self._tls_cert = tls_cert
        self._accept_status = accept_status

    # Access methods

    @property
    def rq_id(self):
        return self._rq_id

    @property
    def method(self):
        return self._method

    @property
    def uri(self):
        return self._uri

    @property
    def body(self):
        return self._body

    @property
    def headers(self):
        return self._headers.copy()

    @property
    def cookies(self):
        return self._cookies.copy()

    @property
    def proxies(self):
        return self._proxies.copy()

    @property
    def auth(self):
        return self._auth

    @property
    def timeout(self):
        return self._timeout

    @property
    def tls_verify(self):
        return self._tls_verify

    @property
    def tls_cert(self):
        return self._tls_cert

    # Helpers

    def __str__(self):
        """
        Return a string representation for debugging purposes.
        """
        return (
            "Request %d: %s of %s\n"
            "\tHeaders: %s\n"
            "\tBody:\n%s" % (self.rq_id, self.method, self.uri, self.headers, self.body)
        )

    def __hash__(self):
        """
        Return a unique hash for the request.
        """
        return hash(self._rq_id)

    # Response methods

    def respond(self, status, headers, content, cookies=None):
        """
        Send a response back to the waiting client.
        """
        if cookies is None:
            cookies = {}

        if ((self._accept_status is None) and (status < 400)) or (
            status in self._accept_status
        ):
            result = HTTPResponse(status, headers.copy(), content, cookies.copy())
        else:
            try:
                raise HTTPStatusError(
                    "HTTP Status %d" % status, status, headers.copy(), content
                )
            except:
                # Catch it for the callback
                result = AsynchronousException()

        self._callback(result)

    def throw(self, exc_class, *args, **kwargs):
        """
        Throw an exception to the client instead.
        """
        try:
            raise exc_class(*args, **kwargs)
        except:
            self._callback(AsynchronousException())
