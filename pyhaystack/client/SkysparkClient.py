# -*- coding: utf-8 -*-

import pyhaystack.client.HaystackClient as hc
import pyhaystack.info as info
import requests
import hmac
import base64
import hashlib
import re


class Connect(hc.Connect):
    """
    This class connects to skyspark and fetch haystack servlet
    A session is open and authentication will persist
    """
    def __init__(self, url, username, password, proj, **kwargs):
        """
        Define skyspark specific local variables : url
        Calls the authenticate function
        """
        proj = str(proj)
        hc.Connect.__init__(self, url, username, password, proj, **kwargs)
        self.loginURL = self.baseURL + "/auth/"+proj+"/api?"+username
        self.saltURL = self.baseURL + "/auth/"+proj+"/salt"
        self.queryURL = self.baseURL + "/api/"+proj+"/"
        self.requestAbout = "/api/"+proj+"/about"
        self.password = password
        self.authenticate()

    def authenticate(self):
        print('pyhaystack %s | Authentication to %s' % (info.__version__,self.loginURL))
        r = requests.get(self.loginURL)
        response_dict = {}

        for line in r.iter_lines():
            key, value = line.split(':')
            response_dict[key] = value
        HMAC= hmac.new(key=self.password, msg=response_dict['username']+":"+response_dict['userSalt'],
                     digestmod=hashlib.sha1)

        h = base64.b64encode(HMAC.digest())
        digest_hash = hashlib.sha1()
        digest_hash.update(h+":"+response_dict['nonce'])
        digest = digest_hash.digest().encode("base64")

        data = {"Content-Type": 'text/plain; charset=utf-8',
                "Host" : self.baseURL,
                "nonce": response_dict['nonce'],
                "digest": digest,
                "password": self.password,
                }
        r = requests.post(self.loginURL, data)
        print r.text
        # """
        # Login to the server
        # Get the cookie from the server, configure headers, make a POST request with credential informations.
        # When connected, ask the haystack for "about" information and print connection information
        # """
        # print('pyhaystack %s | Authentication to %s' % (info.__version__,self.loginURL))
        # print('Initiating connection')
        # try :
        #     # Try to reach server before going further
        #     connection_status = self.s.get(self.loginURL).status_code
        # except requests.exceptions.RequestException as e:
        #     connection_status = 0
        #
        # if connection_status == 200:
        #     print('Initiating authentication')
        #     try:
        #         self.COOKIE = self.s.get(self.loginURL).cookies
        #     except requests.exceptions.RequestException as e:
        #         print('Problem connecting to server : %s' % e)
        #
        #     if self.COOKIE:
        #         try:
        #             self.COOKIEPOSTFIX = self.COOKIE['skyspark_session']
        #             self.headers = {'cookiePostfix' : self.COOKIEPOSTFIX}
        #         except Exception as e:
        #             pass
        #     self.headers =  {'token':'',
        #                      'scheme':'cookieDigest',
        #                      'absPathBase':'/',
        #                      'content-type':'application/x-niagara-login-support',
        #                      'Referer':self.baseURL+'login/',
        #                      'accept':'application/json; charset=utf-8'
        #                     }
        #     # Authentication post request
        #     try:
        #         req = self.s.post(self.loginURL, params=self.headers,auth=(self.USERNAME, self.PASSWORD))
        #         #If word 'login' is in the response page, consider login failed...
        #         print req
        #     except requests.exceptions.RequestException as e:
        #         print('Request POST error : %s' % e)
        # else:
        #     print('Connection failed, check your parameters or VPN connection...')
        #
        # #Continue with haystack login
        # if self.isConnected:
        #     self.about = self.read(self.requestAbout)
        #     self.serverName = self.about['rows'][0]['serverName']
        #     self.haystackVersion = self.about['rows'][0]['haystackVersion']
        #     self.axVersion = self.about['rows'][0]['productVersion']
        #     self.timezone = 'America/' + self.read('read?filter=site')['rows'][0]['tz']
        #     print('Time Zone used : %s' % self.timezone)
        #     print('Connection succeed with haystack on %s (%s) running haystack version %s' %(self.serverName,self.axVersion,self.haystackVersion))
        #     self.refreshHisList()
