#!python
# -*- coding: utf-8 -*-
"""
Tridium Niagara Client support (AX and N4)
"""

from .session import HaystackSession
from .ops.vendor.niagara import NiagaraAXAuthenticateOperation
from .ops.vendor.niagara_scram import Niagara4ScramAuthenticateOperation
from .mixins.vendor.niagara.bql import BQLOperation, BQLMixin
from .mixins.vendor.niagara.encoding import EncodingMixin

import hszinc


class NiagaraHaystackSession(HaystackSession, BQLMixin, EncodingMixin):
    """
    The NiagaraHaystackSession class implements some base support for
    NiagaraAX. This is mainly a convenience for
    collecting the username and password details.
    """

    _AUTH_OPERATION = NiagaraAXAuthenticateOperation
    _BQL_OPERATION = BQLOperation

    def __init__(self, uri, username, password, **kwargs):
        """
        Initialise a Nagara Project Haystack session handler.

        :param uri: Base URI for the Haystack installation.
        :param username: Authentication user name.
        :param password: Authentication password.
        """
        super(NiagaraHaystackSession, self).__init__(uri, "haystack", **kwargs)
        self._username = username
        self._password = password
        self._authenticated = False
        self._uri = uri

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
            (auth, cookies) = operation.result
            self._authenticated = True
            self._client.auth = auth
            self._client.cookies = cookies
        except:
            self._authenticated = False
            self._client.auth = None
            self._client.cookies = None
        finally:
            self._auth_op = None

    def logout(self):
        def callback(response):
            try:
                status_code = response.status_code

            except AttributeError as error:
                status_code = -1

            if status_code != 200:
                self._log.warning("Failed to close nhaystack session")
                self._log.warning("status_code={}".format(status_code))
            else:
                self._log.info("You've been properly disconnected")

        self._get("/logout", callback, api=False)


class Niagara4HaystackSession(HaystackSession, BQLMixin, EncodingMixin):
    """
    The Niagara4HaystackSession class implements some base support for
    Niagara4. This is mainly a convenience for
    collecting the username and password details.
    """

    _AUTH_OPERATION = Niagara4ScramAuthenticateOperation
    _BQL_OPERATION = BQLOperation

    def __init__(self, uri, username, password, grid_format=hszinc.MODE_JSON, **kwargs):
        """
        Initialise a Nagara 4 Project Haystack session handler.

        :param uri: Base URI for the Haystack installation.
        :param username: Authentication user name.
        :param password: Authentication password.
        :param grid_format: the grid format to use in series (json, zinc)
        """
        super(Niagara4HaystackSession, self).__init__(
            uri, "haystack", grid_format=grid_format, **kwargs
        )
        self._username = username
        self._password = password
        self._authenticated = False
        self._uri = uri

    @property
    def is_logged_in(self):
        """
        Return true if the user is logged in.
        """
        return self._authenticated

    # Private methods/properties

    def _on_authenticate_done(self, operation, **kwargs):
        """
        Process the result of an authentication operation.
        """
        try:
            op_result = operation.result
            self._authenticated = op_result["authenticated"]

        except:
            self._authenticated = False
            self._client.auth = None
            self._client.cookies = None
        finally:
            self._auth_op = None

    def logout(self):
        def callback(response):
            try:
                status_code = response.status_code

            except AttributeError as error:
                status_code = -1

            if status_code != 200:
                self._log.warning("Failed to close nhaystack session, ")
                self._log.warning("status_code={}".format(status_code))
            else:
                self._log.info("You've been properly disconnected")

        self._get("/logout", callback, api=False)
