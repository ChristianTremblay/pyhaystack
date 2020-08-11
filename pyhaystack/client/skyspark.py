#!python
# -*- coding: utf-8 -*-
"""
Skyspark Client support
"""

from .session import HaystackSession
from .ops.vendor.skyspark import SkysparkAuthenticateOperation
from .ops.vendor.skyspark_scram import SkysparkScramAuthenticateOperation
from .mixins.vendor.skyspark import evalexpr


class SkysparkHaystackSession(HaystackSession, evalexpr.EvalOpsMixin):
    """
    The SkysparkHaystackSession class implements some base support for
    Skyspark servers.
    """

    _AUTH_OPERATION = SkysparkAuthenticateOperation

    def __init__(self, uri, username, password, project="", **kwargs):
        """
        Initialise a Skyspark Project Haystack session handler.

        :param uri: Base URI for the Haystack installation.
        :param username: Authentication user name.
        :param password: Authentication password.
        :param project: Skyspark project name
        """
        super(SkysparkHaystackSession, self).__init__(uri, "api/%s" % project, **kwargs)
        self._project = project
        self._username = username
        self._password = password
        self._authenticated = False

    @property
    def is_logged_in(self):
        """
        Return true if the user is logged in.
        """
        return self._authenticated

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


class SkysparkScramHaystackSession(HaystackSession, evalexpr.EvalOpsMixin):
    """
    The SkysparkHaystackSession class implements some base support for
    Skyspark servers.
    """

    _AUTH_OPERATION = SkysparkScramAuthenticateOperation

    def __init__(self, uri, username, password, project, **kwargs):
        """
        Initialise a Skyspark Project Haystack session handler.

        :param uri: Base URI for the Haystack installation.
        :param username: Authentication user name.
        :param password: Authentication password.
        :param project: Skyspark project name
        """
        super(SkysparkScramHaystackSession, self).__init__(
            uri, "api/%s" % project, **kwargs
        )

        self._username = username
        self._password = password
        self._project = project
        self._authenticated = False

    @property
    def is_logged_in(self):
        """
        Return true if the user is logged in.
        """
        return self._authenticated

    # Private methods/properties

    def _on_authenticate_done(self, operation, **kwargs):
        """
        Process the result of an authentication operation.  This needs to be
        implemented in the subclass and should, at minimum, set a flag in the
        subclass to indicate the authentication state and clear the _auth_op
        attribute on the base class.
        """
        try:
            op_result = operation.result
            header = op_result["header"]
            self._authenticated = True
            self._client.cookies = None
            self._client.headers = header
        except:
            self._authenticated = False
            self._client.cookies = None
        finally:
            self._auth_op = None

    def __enter__(self):
        """Entering context manager

        usage:
        with SkysparkScramHaystackSession(uri, username, password, project, **kwargs) as session:
            # do whatever with session

        """

        return self

    def __exit__(self, _type, value, traceback):
        """close session when leaving context by trick given by Brian Frank

           https://www.skyfoundry.com/forum/topic/5282#c1

           but beware that this is not standard!"""

            # TODO: Rewrite this when a standard way to close sessions is
            #       implemented in Skyspark.

        def callback(response):
            try:
                status_code = response.status_code

            except AttributeError as error:
                status_code = -1

            if status_code != 200:
                print('Warning: failed to close skyspark session, ', end='')
                print('status_code={}'.format(status_code))

        self._get('/user/logout', callback, api=False)
