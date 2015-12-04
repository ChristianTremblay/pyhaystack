__author__ = 'nick'
#!python
# -*- coding: utf-8 -*-
"""
File : HaystackClient.py (2.x)

"""

import requests
import json



class Connect():
    """
    Abstact class / Make a connection object to haystack server using requests module
    A class must be made for different type of server. See NiagaraAXConnection(HaystackConnection)
    """
    def __init__(self, url, username, password):
        """
        Set local variables
        Open a session object that will be used for connection, with keep-alive feature
            baseURL : http://XX.XX.XX.XX/ - Server URL
            queryURL : ex. for nhaystack = baseURL+haystack = http://XX.XX.XX.XX/haystack
            USERNAME : used for login
            PASSWORD : used for login
            COOKIE : for persistent login
            isConnected : flag to be used for connection related task (don't try if not connected...)
            s : requests.Session() object
            _filteredList : List of histories created by getFilteredHistories
            timezone : timezone from site description
        """
        self.baseURL = url
        self.queryURL = ''
        self.USERNAME = username
        self.PASSWORD = password
        self.COOKIE = ''
        self.isConnected = False
        self.s = requests.Session()
        self._filteredList = []
        self.timezone = 'UTC'


    def authenticate(self):
        """
        This function must be overridden by specific server connection to fit particular needs
        (urls, other conditions)
        """
        myHeader = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'password': self.PASSWORD}
        try:
            r = self.s.post(self.baseURL + '/rest/v1/login/' + self.USERNAME, headers=myHeader)
        except requests.packages.urllib3.exceptions.ProtocolError:
            print "Server is unavailable, Connection Not set"
        else:
            if r.status_code == 200:
                self.isConnected = True



if __name__ == "__main__":
    mango = Connect('http://52.16.65.135:8080', 'admin', 'admin')
    mango.authenticate()
