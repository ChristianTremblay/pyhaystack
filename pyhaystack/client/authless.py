#!python
# -*- coding: utf-8 -*-
"""
Basic Haystack Client for servers that do not support authentication
Based on Skyspark client
"""
import hszinc
from six import string_types

from .mixins.vendor.skyspark import evalexpr
from .session import HaystackSession


class AuthlessHaystackSession(HaystackSession, evalexpr.EvalOpsMixin):
    """
    The AuthlessHaystackSession class implements some base support for
    Haystack servers but doesn't require any authentication. It is based
    on the skyspark client and tested against the sample Java server from
    SkyFoundary.
    """

    _AUTH_OPERATION = None

    def __init__(self, uri, username=None, password=None, project="", **kwargs):
        """
        Initialise an Authless Project Haystack session handler.

        :param uri: Base URI for the Haystack installation.
        :param username: Authentication user name. Ignored.
        :param password: Authentication password. Ignored.
        :param project: Skyspark project name
        """
        super(AuthlessHaystackSession, self).__init__(uri, "%s" % project, **kwargs)
        self._project = project
        self._username = username
        self._password = password
        self._authenticated = False

    @property
    def is_logged_in(self):
        """
        Return true if the user is logged in.
        """
        return True

    # Private methods/properties

    def _on_authenticate_done(self, operation, **kwargs):
        """
        Process the result of an authentication operation.  This needs to be
        implemented in the subclass and should, at minimum, set a flag in the
        subclass to indicate the authentication state and clear the _auth_op
        attribute on the base class.
        """
        try:
            cookies = operation.result
            self._authenticated = True
            self._client.cookies = cookies
        except:
            self._authenticated = False
            self._client.cookies = None
        finally:
            self._auth_op = None
