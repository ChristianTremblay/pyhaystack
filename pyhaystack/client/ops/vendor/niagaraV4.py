from binascii import hexlify, unhexlify, b2a_base64
from base64 import standard_b64encode, b64decode, urlsafe_b64encode
from hashlib import sha256, pbkdf2_hmac
import urllib.error as urlliberror2
import configparser as ConfigParser
import urllib.request as urllib2
import urllib.parse as urlib2_parse
import struct
import hmac
import re
import os
import requests

class Niagara:
    def __init__(self, url, username, password):
        self.url             = url
        self.username        = username
        self.password        = password
        self.client_nonce    = self.get_nonce()
        self.algorithm_name  = "sha256"
        self.algorithm       = sha256
        self.request_session = requests.Session()
        self.request_session.headers.update({"Content-Type": "application/x-niagara-login-support"})

    def get_nonce(self):
        return urlsafe_b64encode( os.urandom(16) ).decode()

    def createClientFirstMessage(self):
        client_first_msg             = "n=%s,r=%s" % (self.username, self.client_nonce)
        return client_first_msg

    def _createClientFinalMessageWithoutProof(self, client_nonce, server_nonce):
        client_final_without_proof = "c=%s,r=%s" % ( standard_b64encode(b'n,,').decode(), server_nonce )
        return client_final_without_proof

    def serverFirstMessage(self, client_first_msg):
        params = 'action=sendClientFirstMessage&clientFirstMessage=n,,%s' % (client_first_msg)

        try:
            self.request_session.headers.update({"Cookie": "niagara_userid=pyhaystack"})
            result = self.request_session.post(self.url, params)
            server_first_msg  = result.text
            tab_response      = server_first_msg.split(",")
            server_nonce      = self.regex_after_equal( tab_response[0] )
            server_salt       = hexlify( b64decode( self.regex_after_equal( tab_response[1] ) ) )
            server_iterations = self.regex_after_equal( tab_response[2] )
            return ( server_first_msg, server_nonce, server_salt, server_iterations )

        except urlliberror2.HTTPError as e:
            print(e)

    def _createAuthMessage(self, client_first_msg, server_first_msg, client_final_without_proof ):
        auth_msg = "%s,%s,%s" % ( client_first_msg, server_first_msg, client_final_without_proof )
        return auth_msg

    def _createClientProof(self, salted_password, auth_msg):
        client_key          = hmac.new( unhexlify( salted_password ), "Client Key".encode('UTF-8'), self.algorithm).hexdigest()
        stored_key          = self._hash_sha256( unhexlify(client_key) )
        client_signature    = hmac.new( unhexlify( stored_key ) , auth_msg.encode() , self.algorithm ).hexdigest()
        client_proof        = self._xor (client_key, client_signature)
        return b2a_base64(unhexlify(client_proof)).decode()

    def _createServerSignature(self, auth_msg, salted_password):
        server_key       = hmac.new( unhexlify( salted_password ), "Server Key".encode('UTF-8'), self.algorithm).hexdigest()
        server_signature = hmac.new( unhexlify( server_key ) , auth_msg.encode() , self.algorithm ).hexdigest()
        return server_signature

    def processServerFinalMessage(self, server_final_message, auth_msg, salted_password):

        print("ServerFinalMessage: " + server_final_message)
        serverSignature = self._createServerSignature( auth_msg, salted_password )
        remote_server_signature = hexlify( b64decode( self.regex_after_equal( server_final_message ) ) )

        if serverSignature == remote_server_signature.decode():
            print("Remote Server Signature Accepted")
        else:
            print("Server Validation failed")

    def scram_authentication(self):
        client_first_msg                                                   = self.createClientFirstMessage()
        ( server_first_msg, server_nonce, server_salt, server_iterations ) = self.serverFirstMessage( client_first_msg )
        salted_password                                                    = self.salted_password( server_salt, server_iterations )
        client_final_without_proof                                         = self._createClientFinalMessageWithoutProof( self.client_nonce, server_nonce )
        auth_msg                                                           = self._createAuthMessage( client_first_msg, server_first_msg, client_final_without_proof )
        client_proof                                                       = self._createClientProof( salted_password, auth_msg ) #Good
        client_final_message                                               = client_final_without_proof + ",p=" + client_proof
        final_msg = 'action=sendClientFinalMessage&clientFinalMessage=%s' % (client_final_message)

        #TODO: We may find a way to use the same request_session without creating a new requests.Session()
        try:
            s = requests.Session()
            s.cookies = self.request_session.cookies
            s.headers.update({"Content-Type": "application/x-niagara-login-support"})
            result = s.post( self.url, final_msg.strip() )
            server_final_message = result.text
            self.processServerFinalMessage( server_final_message, auth_msg, salted_password )

        except urlliberror2.HTTPError as e:
            print(e)

    def _hash_sha256(self, str):
        hashFunc = self.algorithm()
        hashFunc.update( str )
        return hashFunc.hexdigest()

    def salted_password(self, salt, iterations):
        dk = pbkdf2_hmac( self.algorithm_name, self.password.encode(), unhexlify(salt), int(iterations))
        encrypt_password = hexlify(dk)
        return encrypt_password

    def regex_after_equal(self, s):
        tmp_str = re.search( "\=(.*)$" ,s, flags=0)
        return tmp_str.group(1)


    def _xor(self, s1, s2):
        return hex(int(s1, 16) ^ int(s2, 16))[2:]

niagara = Niagara("http://69.168.136.66:88/j_security_check/", "pyhaystack", "PWhaystack1" )
auth_token = niagara.scram_authentication()
