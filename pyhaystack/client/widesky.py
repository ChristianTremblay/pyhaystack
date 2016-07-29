#!python
# -*- coding: utf-8 -*-
"""
VRT Widesky Client support
"""

from time import time
from .session import HaystackSession
from .ops.vendor.widesky import WideskyAuthenticateOperation, \
        CreateEntityOperation, WideSkyHasFeaturesOperation
from .mixins.vendor.widesky import crud, multihis

class WideskyHaystackSession(crud.CRUDOpsMixin,
        multihis.MultiHisOpsMixin,
        HaystackSession):
    """
    The WideskyHaystackSession class implements some base support for
    NiagaraAX and Niagara4 servers.  This is mainly a convenience for
    collecting the username and password details.
    """

    _AUTH_OPERATION = WideskyAuthenticateOperation
    _CREATE_ENTITY_OPERATION = CreateEntityOperation
    _HAS_FEATURES_OPERATION = WideSkyHasFeaturesOperation

    def __init__(self, uri, username, password,
            client_id, client_secret,
            api_dir='api', auth_dir='oauth2/token', **kwargs):
        """
        Initialise a VRT Widesky Project Haystack session handler.

        :param uri: Base URI for the Haystack installation.
        :param username: Authentication user name.
        :param password: Authentication password.
        :param client_id: Authentication client ID.
        :param client_secret: Authentication client secret.
        """
        super(WideskyHaystackSession, self).__init__(
                uri, api_dir, **kwargs)
        self._auth_dir = auth_dir
        self._username = username
        self._password = password
        self._client_id = client_id
        self._client_secret = client_secret
        self._auth_result = None

    @property
    def is_logged_in(self):
        """
        Return true if the user is logged in.
        """
        if self._auth_result is None:
            return False
        # Return true if our token expires in the future.
        return (self._auth_result.get('expires_in') or 0.0) > (1000.0 * time())

    # Private methods/properties

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
                    'Authorization': '%s %s' % (
                        self._auth_result['token_type'],
                        self._auth_result['access_token'],
                    )
            }
        except:
            self._auth_result = None
            self._client.headers = {}
            self._log.warning('Log-in fails', exc_info=1)
        finally:
            self._auth_op = None
