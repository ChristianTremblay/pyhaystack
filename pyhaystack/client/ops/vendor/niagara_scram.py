#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Skyspark operation implementations.
"""

import fysom
import hmac
import base64
import hashlib
import re

from hashlib import sha1, sha256, pbkdf2_hmac
from binascii import b2a_hex, unhexlify, b2a_base64, hexlify

from ....util import state, scram
from ....util.asyncexc import AsynchronousException
from ...http.exceptions import HTTPStatusError

class Niagara4ScramAuthenticateOperation(state.HaystackOperation):
    """
    An implementation of the log-in procedure for Skyspark.  The procedure
    is as follows:

    1. Hello -> initiate the authentication conversation, sending the username we wish to authenticate as.
    2. First Message -> Send an authentication request to the server using the user name and a nonce
    3. Second Message -> Send an encoded message that proves we have the password.
    4. Retrieve the authToken send back by the server
    5. Optional -> Verifying that we are communicating with the correct server
    6. Using AuthToken to send request to the SkySpark Rest API: Authorization: BEARER authToken=aaabbbcccddd

    Future requests should the cookies returned.
    """

    _COOKIE_RE = re.compile(r'^cookie[ \t]*:[ \t]*([^=]+)=(.*)$')

    def __init__(self, session, retries=0):
        """
        Attempt to log in to the Skyspark server.

        :param session: Haystack HTTP session object.
        :param retries: Number of retries permitted in case of failure.
        """

        super(Niagara4ScramAuthenticateOperation, self).__init__()
        self._retries = retries
        self._session = session
        self._cookie = None
        self._nonce = None
        self._username = None
        self._user_salt = None
        self._digest = None

        self._algorithm = None
        self._handshake_token = None
        self._server_first_msg  = None
        self._server_nonce = None
        self._server_salt = None
        self._server_iterations = None
        self._auth_token = None
        self._auth = None

        self._login_uri = '%s'   % \
                (session._client.uri)
        self._state_machine = fysom.Fysom(
                initial='init', final='done',
                events=[
                    # Event               Current State         New State
                    ('get_new_session',   'init',               'newsession'),
                    ('do_hs_token',       'newsession',         'handshake_token'),
                    ('do_second_msg',     'handshake_token',    'second_msg'),
                    ('do_validate_second','second_msg',         'authenticated'),
                    ('login_done',        'authenticated',      'done'),
                    ('exception',         '*',                  'failed'),
                    ('retry',             'failed',             'newsession'),
                    ('abort',             'failed',             'done'),
                ], callbacks={
                    'onenternewsession':        self._do_new_session,
                    'onenterhandshake_token':   self._do_hs_token,
                    'onentersecond_msg':        self._do_second_msg,
                    'onenterauthenticated':     self._do_authenticated,
                    'onenterfailed':            self._do_fail_retry,
                    'onenterdone':              self._do_done,
                })

    def go(self):
        """
        Start the request.
        """
        # Are we logged in?
        print('Go')
        try:
            self._state_machine.get_new_session()
        except: # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _do_new_session(self, event):
        """
        Test if server respond...
        """
        print('do_new', self._login_uri)
        self._session._client._session.cookies.clear()
        try:
            self._session._get('%s/prelogin?clear=true' % self._login_uri,
                    callback=self._on_new_session,
                    cookies={}, headers={}, exclude_cookies=True,
                    api=False)
        except: # Catch all exceptions to pass to caller.
            pass

    def _on_new_session(self, response):
        try:
            print(response.headers)
            
        
            self._state_machine.do_hs_token()
            
        except Exception as e: # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _do_hs_token(self, event):
        """
        Test if server respond...
        """
        print('do_hs_token', self._login_uri)
        try:
            self._session._post('%s/prelogin' % self._login_uri,
                    params={'j_username': self._session._username},
                    callback=self._on_hs_token,
                    cookies={}, 
                    headers={}, 
                    api=False)
        except: # Catch all exceptions to pass to caller.
            pass        

    def _on_hs_token(self, response):
        """
        Retrieve the log-in parameters.
        """
        print('on_hs_token', response.headers)
        
        try:
            #if isinstance(response, AsynchronousException):
            #    response.reraise()
            
            self._nonce = scram.get_nonce_16()
            self._salt_username = scram.base64_no_padding(self._session._username)
            self.client_first_msg = "n=%s,r=%s" % (self._session._username, self._nonce)
            self._state_machine.do_second_msg()
        except Exception as e: # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _do_second_msg(self, event):
        print('do_second_msg')
        msg = 'action=sendClientFirstMessage&clientFirstMessage=n,,%s' % self.client_first_msg
        cookies = dict(niagara_userid = self._session._username)
        try:
            self._session._post('%s/j_security_check' % (self._login_uri),
                    body=msg.encode('utf-8'),
                    callback=self._on_second_msg,
                    headers={"Content-Type": "application/x-niagara-login-support",
                             "Connection": "Keep-Alive",
                             "Referer": '%s/login'%self._login_uri,
                             "Accept-Encoding": "gzip, deflate",
                             "Accept": "text/html, application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
                    #cookies=cookies,
                    api=False)
        except Exception as e:
            self._state_machine.exception(result=AsynchronousException())

    def _on_second_msg(self, response):
        print('on second msg')
        try:
            response.reraise() # ← AsynchronousException class
        except HTTPStatusError as e:
            if e.status != 401 and e.status != 303 and e.status != 500:
                raise
            else:
                response = e
        except AttributeError:
            pass
        try:
            print('do validate hs token', response.headers)
#        try:
#            response.reraise() # ← AsynchronousException class
#        except HTTPStatusError as e:
#            if e.status != 401 and e.status != 303:
#                raise

            self.jsession = get_jession(response.headers['set-cookie'])
            print('JSESSION : ', self.jsession)
            self.server_first_msg  = response.body.decode('utf-8')	
            print("ServerFirstMessage: " + self.server_first_msg)
            tab_response = self.server_first_msg.split(",")
            self.server_nonce = scram.regex_after_equal( tab_response[0] )
            self.server_salt = hexlify( scram.b64decode( scram.regex_after_equal( tab_response[1] ) ) )
            self.server_iterations = scram.regex_after_equal( tab_response[2] )
            self._algorithm_name = "sha256"
            self._algorithm = sha256
            
            print('Nonce :', self.server_nonce, '\n',
                  'Server Salt :', self.server_salt, '\n',
                  'Server iter :', self.server_iterations)
    
            #self._handshake_token = scram.regex_after_equal(header_response[0])
            self._state_machine.do_validate_second()
        except Exception as e:
            self._state_machine.exception(result=AsynchronousException())


    def _do_authenticated(self, event):
        print('do auth msg')
        self.salted_password = scram.salted_password_2( self.server_salt, self.server_iterations, self._algorithm_name, self._session._password )
        print('Salted password :', self.salted_password)
        client_final_without_proof = "c=%s,r=%s" % ( scram.standard_b64encode(b'n,,').decode(), 
                                                    self.server_nonce )
        print('Client final wo proof :', client_final_without_proof)
        self.auth_msg = "%s,%s,%s" % ( self.client_first_msg, self.server_first_msg, 
                                      client_final_without_proof )
                
        print('Auth msg :', self.auth_msg)
        
        client_proof = _createClientProof(self.salted_password, self.auth_msg, self._algorithm)
        client_final_message = client_final_without_proof + ",p=" + client_proof
        final_msg = 'action=sendClientFinalMessage&clientFinalMessage=%s' % (client_final_message)
        #self._session._client._session.headers.update({'Cookie': 'niagara_userid=%s,JSESSIONID=%s' % (self._session._username, self.jsession)})
        print('Final Msg : ', final_msg)
        print('Session headers : ', self._session._client._session.headers)
        cookies = dict(niagara_userid = self._session._username,
                       JSESSIONID = self.jsession)
        try:
            # Post
            self._session._post('%s/j_security_check' % self._login_uri,
                    body=final_msg.strip().encode("utf-8"),
                    callback=self._on_authenticated,
                    headers={"Content-Type": "application/x-niagara-login-support"},
                    #headers={},
                    #cookies=cookies,
                    api=False)
        except:
            self._state_machine.exception(result=AsynchronousException())

    def _on_authenticated(self, response):
        print('on_authenticated', response.headers)
        try:
            response.reraise() # ← AsynchronousException class
        except HTTPStatusError as e:
            if e.status != 401 and e.status != 303:
                raise
            else:
                print('Error : ', e)
                response = e
        except AttributeError:
            pass        
        try:
            server_final_message = response.body.decode('utf-8')
            server_key = hmac.new( unhexlify( self.salted_password ), "Server Key".encode('UTF-8'), self._algorithm).hexdigest()
            server_signature = hmac.new( unhexlify( server_key ) , self.auth_msg.encode() , self._algorithm ).hexdigest()
            remote_server_signature = hexlify( scram.b64decode( scram.regex_after_equal( server_final_message ) ) )
            
            if server_signature == remote_server_signature.decode():
                print("Remote Server Signature Accepted")
                print(server_final_message)
                #self._session._client._session.cookies.clear()
                self._state_machine.login_done(result={'cookie': dict(JSESSIONID=self.jsession,
                                                                      niagara_userid=self._session._username)})
            else:
                print("Server Validation failed")
                raise Exception('Login Failed')
            
#                header_response = e.headers['WWW-Authenticate']
#                tab_header = header_response.split(',')
#                server_data = scram.regex_after_equal(tab_header[0])
#                missing_padding = len(server_data) % 4
#                if missing_padding != 0:
#                    server_data += '='* (4 - missing_padding)
#                server_data = scram.b64decode(server_data).decode()
#                tab_response = server_data.split(',')
#                self._server_first_msg = server_data
#                self._server_nonce = scram.regex_after_equal(tab_response[0])
#                self._server_salt = scram.regex_after_equal(tab_response[1])
#                self._server_iterations = scram.regex_after_equal(tab_response[2])
#                if not self._server_nonce.startswith(self._nonce):
#                    raise Exception("Server returned an invalid nonce.")

#                self._state_machine.do_server_token()
            #print(self._session._client._session.get('%s/haystack/about' % self._login_uri))
            #self._state_machine.login_done(result={'cookie': dict(JSESSIONID=self.jsession)})

        except Exception as e:
             self._state_machine.exception(result=AsynchronousException())

    def _do_fail_retry(self, event):
        """
        Determine whether we retry or fail outright.
        """
        if self._retries > 0:
            self._retries -= 1
            self._state_machine.retry()
        else:
            self._state_machine.abort(result=event.result)

    def _do_done(self, event):
        """
        Return the result from the state machine.
        """
        print('Done')
        self._done(event.result)

#def get_digest_info(param):
#    message = binary_encoding("%s:%s" % (param['username'], param['userSalt']))
#    password_buf = binary_encoding(param['password'])
#    hmac_final = base64.b64encode(hmac.new(key=password_buf, msg=message, digestmod=hashlib.sha1).digest())
#
#    digest_msg = binary_encoding('%s:%s' % (hmac_final.decode('utf-8'), param['nonce']))
#    digest = hashlib.sha1()
#    digest.update(digest_msg)
#    digest_final = base64.b64encode((digest.digest()))
#
#    res ={'hmac' : hmac_final.decode('utf-8'),
#         'digest' : digest_final.decode('utf-8'),
#         'nonce' : param['nonce']}
#    return res

def binary_encoding(string, encoding = 'utf-8'):
    """
    This helper function will allow compatibility with Python 2 and 3
    """
    try:
        return bytes(string, encoding)
    except TypeError: # We are in Python 2
        return str(string)

def get_jession(arg_header):
    #revDct = dict((val, key) for (key, val) in arg_header )
    set_cookie = arg_header.split(',')
    print('GET JSESSION : ', arg_header)
#    return jsession
    for key in set_cookie:
        if "JSESSIONID=" in key:
            jsession = scram.regex_after_equal(key)
            jsession = jsession.split(";")[0]
            return jsession
        
def _createClientProof(salted_password, auth_msg, algorithm):
    client_key          = hmac.new( unhexlify( salted_password ), "Client Key".encode('UTF-8'), algorithm).hexdigest()
    stored_key          = scram._hash_sha256( unhexlify(client_key), algorithm )
    client_signature    = hmac.new( unhexlify( stored_key ) , auth_msg.encode() , algorithm ).hexdigest()
    client_proof        = scram._xor (client_key, client_signature)
    return b2a_base64(unhexlify(client_proof)).decode('utf-8')

