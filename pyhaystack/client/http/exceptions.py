# -*- coding: utf-8 -*-
"""
HTTP client exception classes.
"""


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

    def __init__(self, message, status, headers=None, body=None):
        self.headers = headers
        self.body = body
        self.status = status
        super(HTTPStatusError, self).__init__(message, status)
