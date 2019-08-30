# -*- coding: utf-8 -*-
"""
pyhaystack Custom exceptions

"""


class HaystackError(Exception):
    """
    Exception thrown when an error grid is returned by the Haystack server.
    See http://project-haystack.org/doc/Rest#errorGrid
    """

    def __init__(self, message, traceback=None, *args, **kwargs):
        super(HaystackError, self).__init__(message, *args, **kwargs)
        self.traceback = traceback


# Those exceptions have been made when working with Niagara AX
class NoResponseFromServer(Exception):
    pass


class ProblemSendingRequestToServer(Exception):
    pass


class NoCookieReceived(Exception):
    pass


class ProblemReadingCookie(Exception):
    pass


class AuthenticationProblem(Exception):
    pass


class UnknownHistoryType(Exception):
    pass
