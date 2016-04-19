# -*- coding: utf-8 -*-
"""
Synchronous HTTP client using Python Requests.
"""

from .base import HTTPClient, HTTPResponse
from .auth import BasicAuthenticationCredentials, \
                    DigestAuthenticationCredentials
from .exceptions import HTTPConnectionError, HTTPTimeoutError, \
        HTTPRedirectError, HTTPStatusError, HTTPBaseError

from ...util.asyncexc import AsynchronousException

import requests

class SyncHttpClient(HTTPClient):
    def __init__(self, **kwargs):
        self._session = requests.Session()
        super(SyncHttpClient, self).__init__(**kwargs)

    def _request(self, method, uri, callback, body = None,
            headers = None, cookies = None, auth = None, timeout = None, proxies = None,
            tls_verify = None, tls_cert = None):

        print('sync : request')
        if auth is not None:
            print('auth not none : %s' % auth.username)
            if isinstance(auth, BasicAuthenticationCredentials):               
                auth = requests.auth.HTTPBasicAuth(
                        auth.username, auth.password)
                #auth = (auth.username, auth.password)
                print('basic auth : %s' % auth)
            elif isinstance(auth, DigestAuthenticationCredentials):             
                auth = requests.auth.HTTPDigestAuth(
                        auth.username, auth.password)
                print('digest auth : %s' % auth)
            else:
                print('problem with auth')
                raise NotImplementedError(
                        '%s does not implement support for %s' % (
                            self.__class__.__name__,
                            auth.__class__.__name__))

        try:
            print('sync global try')
            try:
                print('building request : %s' % method)
                response = self._session.request(
                        method=method, url=uri, data=body, headers=headers,
                        cookies=cookies, auth=auth, timeout=timeout,
                        proxies=proxies, verify=tls_verify, cert=tls_cert)
                #print('Response : %s' % response.text)
                # Can't use raise_for_status as error 404 may be sent
                # by the Jace even if login succeeded
                #response.raise_for_status()
                print('==status code==', response.status_code)
                print('===header==', dict(response.headers))
                #print('=== content ===', response.content)
                print('=== cookies ===', dict(response.cookies))
                callback(HTTPResponse(response.status_code, 
                                      dict(response.headers), 
                                      response.content, 
                                      dict(response.cookies),
                                      response.text
                                      )
                                      )
            # Error 404 cannot be trusted... may be OK
            #except requests.exceptions.HTTPError as e:
            #    print('http error')
            #    raise HTTPStatusError(e.message, e.response.status_code, \
            #            dict(e.response.headers), e.response.content)
            except requests.exceptions.Timeout as e:
                print('timeout error')
                raise HTTPTimeoutError(e.strerror)
            except requests.exceptions.TooManyRedirects as e:
                print('redirect error')
                raise HTTPRedirectError(e.message)
            except requests.exceptions.ConnectionError as e:
                print('connection error')
                raise HTTPConnectionError(e.strerror, e.errno)
            except requests.exceptions.RequestException:
                print('request error')
                # TODO: handle this with a more specific exception
                raise HTTPBaseError(e.message)
        except:
            print('http client error')
            # Catch all exceptions and forward those to the callback function
            callback(AsynchronousException())
