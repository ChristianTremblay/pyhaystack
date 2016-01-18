# -*- coding: utf-8 -*-
"""
@author: Stuart Longland
Based on NiagaraAX client code.
"""
from . import HaystackClient as hc
from .. import info as info
import requests
import json
import time
from hszinc import zoneinfo

class Connect(hc.Connect):
    """
    This class connects to Widesky and fetch haystack servlet
    A session is open and authentication will persist
    """
    def __init__(self,url,username,password,**kwargs):
        """
        Define Niagara AX specific local variables : url
        Calls the authenticate function
        """
        hc.Connect.__init__(self,url,username,password,**kwargs)
        self.loginURL = self.baseURL + "login/"
        self.queryURL = self.baseURL + "api/"
        self._login_expiry = 0
        self.isConnected = property(lambda self : \
                self._login_expiry > time.time())
        self.authenticate()

    def authenticate(self):
        """
        Login to the server
        Get the cookie from the server, configure headers, make a POST request with credential informations.
        When connected, ask the haystack for "about" information and print connection information
        """

        # Source: https://vrtsystems.atlassian.net/wiki/display/WSDOC/WideSky+API+Reference
        # Authentication
        #
        # WideSky uses token-based authentication with a bcrypt key hashing.
        # Before accessing the API, the client must first request a token, by
        # supplying a valid username & password with a POST request to the
        # /login URI. For example:
        #
        # POST /login
        # Content-Type: application/json
        #
        # {
        #
        #  "username": "myuser",
        #  "password": "mypassword"
        # }
        #
        # Response:
        #
        # {
        #   "token": "eyJ0…h1-Q",
        #   "expires": 1448250270588,
        #   "user": {
        #     "name": "myuser",
        #     "role": "admin",
        #     …
        #   }
        # }

        # Request body
        rq_body = json.dumps({
            'username': self.USERNAME,
            'password': self.PASSWORD,
        })

        # Attempt to post to login URL, this may throw back an exception.
        response = self.s.post(self.loginURL, headers={
                'Content-Type': 'application/json',
            }, data=rq_body)
        # See if something failed, this will raise a HTTPError if something
        # failed at the server end.
        response.raise_for_status()

        # All good, keep moving along.
        res_body = response.json()
        self._rq_headers['X-Access-Token'] = res_body.get('token')
        self._login_expiry = res_body.get('expiry',0)

        #Continue with haystack login
        if self.isConnected:
            about = self._get_grid('about')
            versionInfo = about[0]
            self.serverName = versionInfo['serverName']
            self.haystackVersion = versionInfo['haystackVersion']
            haystack_tz = zoneinfo.get_tz_map()
            self.timezone = haystack_tz[self._get_grid('read?filter=site')[0]['tz']]
            self._log.getChild('authenticate').debug(
                    'Connected to haystack instance on %s '\
                            '(protocol %s, implementation %s %s).  '\
                            'Time Zone used : %s',
                            self.serverName,
                            self.haystackVersion,
                            versionInfo.get('productName','Unknown'),
                            versionInfo.get('productVersion','Unknown'),
                            self.timezone)
            self.refreshHisList()
        else:
            # TODO: better exception
            raise Exception('Log-in failed.')
