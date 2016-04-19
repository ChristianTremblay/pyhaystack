    # -*- coding: utf-8 -*-
"""
Created on Tue Nov 18 13:44:20 2014

@author: CTremblay
"""
import pyhaystack.client.HaystackClient as hc
import pyhaystack.info as info
import requests
import re

class Connect(hc.Connect):
    """
    This class connects to NiagaraAX and fetch haystack servlet
    A session is open and authentication will persist
    """
    def __init__(self,url,username,password,*, refreshHisList = True, **kwargs):
        """
        Define Niagara AX specific local variables : url
        Calls the authenticate function
        """
        hc.Connect.__init__(self,url,username,password,**kwargs)
        self.logoutURL = self.baseURL + "logout/"
        self.loginURL = self.baseURL + "login/"
        self.preloginURL = self.baseURL + "prelogin/"
        self.queryURL = self.baseURL + "haystack/"
        self.requestAbout = "about"
        self.authenticate(refreshHisList = refreshHisList)

    def _get_kwargs(self, **kwargs):
        if 'auth' not in kwargs:
            kwargs['auth'] = (self.USERNAME, self.PASSWORD)
        return super(Connect, self)._get_kwargs(**kwargs)

    def authenticate(self, refreshHisList = True):
        """
        Login to the server
        Get the cookie from the server, configure headers, make a POST request with credential informations.
        When connected, ask the haystack for "about" information and print connection information
        """
        print('pyhaystack %s | Authentication to %s' % (info.__version__,self.loginURL))
        print('Initiating connection')
        try :
            # Try to reach server before going further
            connection_status = self.s.get(self.baseURL).status_code
        except requests.exceptions.RequestException as e:
            connection_status = 0

        if connection_status == 200:
            print('Initiating authentication')
            try:
                self.COOKIE = self.s.get(self.loginURL).cookies
            except requests.exceptions.RequestException as e:
                print('Problem connecting to server : %s' % e)

            if self.COOKIE:
                try:
                    self.COOKIEPOSTFIX = self.COOKIE['niagara_session']
                    self.headers = {'cookiePostfix' : self.COOKIEPOSTFIX}
                except Exception as e:
                    pass
            self.headers =  {'token':'',
                             'scheme':'cookieDigest',
                             'absPathBase':'/',
                             'content-type':'application/x-niagara-login-support',
                             'Referer':self.baseURL+'login/',
                             'accept':'application/json; charset=utf-8',
                             'Accept-Encoding': 'gzip'
                            }
            # Authentication post request
            try:
                req = self.s.post(self.preloginURL, params=self.headers,auth=(self.USERNAME))
                #If word 'login' is in the response page, consider login failed...
                if re.search(re.compile('login', re.IGNORECASE), req.text):
                    self.isConnected = False
                    print('Connection failure, check credentials')
                else:
                    req = self.s.post(self.loginURL, params=self.headers,auth=(self.USERNAME, self.PASSWORD))
                    if re.search(re.compile('login', re.IGNORECASE), req.text):
                        self.isConnected = False
                        print('Connection failure, check credentials')
                    else:
                        self.isConnected = True
                        print('User logged in...')
            except requests.exceptions.RequestException as e:
                print('Request POST error : %s' % e)
        else:
            print('Connection failed, check your parameters or VPN connection...')

        #Continue with haystack login
        if self.isConnected:
            about = self._get_grid(self.requestAbout)
            self.serverName = about[0]['serverName']
            self.haystackVersion = about[0]['haystackVersion']
            self.axVersion = about[0]['productVersion']
            self.timezone = 'America/' + self._get_grid('read?filter=site')[0]['tz']
            print('Time Zone used : %s' % self.timezone)
            print('Connection succeed with haystack on %s (%s) running haystack version %s' %(self.serverName,self.axVersion,self.haystackVersion))
        if refreshHisList:
            self.refreshHisList()

    def disconnect(self):
        self.s.get(self.logoutURL)
