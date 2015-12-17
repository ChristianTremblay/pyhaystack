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
        self.loginURL = self.baseURL + "/auth/" + proj + "/api?" + username
        self.saltURL = self.baseURL + "/auth/" + proj + "/salt"
        self.queryURL = self.baseURL + "/api/" + proj + "/"
        self.requestAbout = "about"
        self.password = password
        self.authenticate()

    def authenticate(self):
        print('pyhaystack %s | Authentication to %s' % (info.__version__, self.loginURL))
        r = self.s.get(self.loginURL)
        response_dict = {}

        for line in r.iter_lines():
            key, value = line.split(':')
            response_dict[key] = value
        HMAC = hmac.new(key=self.password, msg=response_dict['username'] + ":" + response_dict['userSalt'],
                        digestmod=hashlib.sha1)

        h = base64.b64encode(HMAC.digest())
        digest_hash = hashlib.sha1()
        digest_hash.update(h + ":" + response_dict['nonce'])
        digest = digest_hash.digest().encode("base64").rstrip('\n')

        head = {"Content-Type": 'text/plain',
                "Host": self.baseURL,
                "User-Agent": 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',
                "charset": 'utf-8'
                }
        data = "nonce:" + response_dict['nonce'] + "\ndigest:" + digest
        r = requests.Request(method='POST', url=self.loginURL, headers=head, data=data)
        prepared = r.prepare()

        def pretty_print_POST(req):
            """
            At this point it is completely built and ready
            to be fired; it is "prepared".

            However pay attention at the formatting used in
            this function because it is programmed to be pretty
            printed and may differ from the actual request.
            """
            print('{}\n{}\n{}\n\n{}'.format(
                '-----------START-----------',
                req.method + ' ' + req.url,
                '\n'.join('{}:{}'.format(k, v) for k, v in req.headers.items()),
                req.body,
            ))

        r = self.s.send(prepared)
        if str(r.text).find("cookie") != -1:
            self.isConnected = True
            self.s.cookies.set(str(r.text).split(":")[1].split("=")[0], str(r.text).split(":")[1].split("=")[1])

        if self.isConnected:
            self.about = self.read(self.requestAbout)
            self.serverName = self.about['rows'][0]['serverName']
            self.haystackVersion = self.about['rows'][0]['haystackVersion']
            self.axVersion = self.about['rows'][0]['productVersion']
            self.timezone = self.about['rows'][0]['tz']
            print('Time Zone used : %s' % self.timezone)
            print('Connection succeed with haystack on %s (%s) running haystack version %s' % (
                self.serverName, self.axVersion, self.haystackVersion))
