#!python
# -*- coding: utf-8 -*-
"""
VRT Widesky Client support
"""

from time import time
from .session import HaystackSession
from .ops.vendor.widesky import (
    WideskyAuthenticateOperation,
    CreateEntityOperation,
    WideSkyHasFeaturesOperation,
    WideSkyPasswordChangeOperation,
)
from .mixins.vendor.widesky import crud, multihis, password
from ..util.asyncexc import AsynchronousException
from .http.exceptions import HTTPStatusError


def _decode_str(s, enc="utf-8"):
    """
    Try to decode a 'str' object to a Unicode string.
    """
    try:
        return s.decode(enc)
    except AttributeError:
        # This is probably already a Unicode string
        return s


class WideskyHaystackSession(
    crud.CRUDOpsMixin,
    multihis.MultiHisOpsMixin,
    password.PasswordOpsMixin,
    HaystackSession,
):
    """
    The WideskyHaystackSession class implements some base support for
    Widesky servers.  This is mainly a convenience for
    collecting the username and password details.
    """

    _AUTH_OPERATION = WideskyAuthenticateOperation
    _CREATE_ENTITY_OPERATION = CreateEntityOperation
    _HAS_FEATURES_OPERATION = WideSkyHasFeaturesOperation
    _PASSWORD_CHANGE_OPERATION = WideSkyPasswordChangeOperation

    def __init__(
        self,
        uri,
        username,
        password,
        client_id,
        client_secret,
        api_dir="api",
        auth_dir="oauth2/token",
        impersonate=None,
        **kwargs
    ):
        """
        Initialise a VRT Widesky Project Haystack session handler.

        :param uri: Base URI for the Haystack installation.
        :param username: Authentication user name.
        :param password: Authentication password.
        :param client_id: Authentication client ID.
        :param client_secret: Authentication client secret.
        :param impersonate: A widesky user ID to impersonate (or None)
        """
        super(WideskyHaystackSession, self).__init__(uri, api_dir, **kwargs)
        self._auth_dir = auth_dir
        self._username = username
        self._password = password
        self._client_id = client_id
        self._client_secret = client_secret
        self._auth_result = None
        self._impersonate = impersonate

    @property
    def is_logged_in(self):
        """
        Return true if the user is logged in.
        """
        if self._auth_result is None:
            return False
        # Return true if our token expires in the future.
        return (self._auth_result.get("expires_in") or 0.0) > (1000.0 * time())

    # Private methods/properties

    def _on_read(self, ids, filter_expr, limit, callback, **kwargs):
        return super(WideskyHaystackSession, self)._on_read(
            ids, filter_expr, limit, callback, accept_status=(200, 404)
        )

    def _on_http_grid_response(self, response):
        # If there's a '401' error, then we've lost the token.
        if isinstance(response, AsynchronousException):
            try:
                response.reraise()
            except HTTPStatusError as e:
                status_code = e.status
            except:
                # Anything else, no-op … let the state machine handle it!
                return
        else:
            status_code = response.status_code

        if (status_code == 401) and (self._auth_result is not None):
            self._log.warning("Authentication lost due to HTTP error 401.")
            self._auth_result = None
            self._client.headers = {}

    def _on_authenticate_done(self, operation, **kwargs):
        """
        Process the result of an authentication operation.  This needs to be
        implemented in the subclass and should, at minimum, set a flag in the
        subclass to indicate the authentication state and clear the _auth_op
        attribute on the base class.
        """
        try:
            self._auth_result = operation.result
            self._client.headers = {
                "Authorization": (
                    u"%s %s"
                    % (
                        _decode_str(self._auth_result["token_type"], "us-ascii"),
                        _decode_str(self._auth_result["access_token"], "us-ascii"),
                    )
                ).encode("us-ascii")
            }

            if self._impersonate:
                self._client.headers["X-IMPERSONATE"] = self._impersonate
        except:
            self._auth_result = None
            self._client.headers = {}
            self._log.warning("Log-in fails", exc_info=1)
        finally:
            self._auth_op = None
