from binascii import b2a_hex, unhexlify, b2a_base64, hexlify
from requests.auth import HTTPBasicAuth
from base64 import standard_b64encode, b64decode, urlsafe_b64encode, urlsafe_b64decode
from hashlib import sha1, sha256, pbkdf2_hmac

import urllib.error as urlliberror2
import configparser as ConfigParser
import urllib.request as urllib2
import logging
import hmac
import re
import os

# You must initialize logging, otherwise you'll not see debug output.
#logging.basicConfig()
#logging.getLogger().setLevel(logging.DEBUG)
#requests_log = logging.getLogger("requests.packages.urllib3")
#requests_log.setLevel(logging.DEBUG)
#requests_log.propagate = True

class SkySpark:
    def __init__(self, url, login, password):
        self.url             = url
        self.login           = login
        self.password        = password
        self.client_nonce    = self.get_nonce()
        self.handshake_token = self.get_handshakeToken()

    def get_nonce(self):
        return b2a_hex(os.urandom(32)).decode()

    def get_handshakeToken(self): #Good
        login_base64         = self.base64_no_padding( self.login )
        request              = urllib2.Request(self.url)
        client_first_message = "HELLO username=%s" % (login_base64)
        request.add_header("Authorization", client_first_message )

        try:
            result = urllib2.urlopen(request)
        except urlliberror2.HTTPError as e:
            server_response      = e.headers['WWW-Authenticate']
            header_response      = server_response.split(',')
            algorithm = self.regex_after_equal( header_response[1] )
            self.algorithm_name = algorithm.replace("-", "").lower()

            if self.algorithm_name == "sha256":
                self.algorithm = sha256
            elif self.algorithm_name == "sha1":
                self.algorithm = sha1
            else:
                raise Exception("SHA no imported yet")

            return self.regex_after_equal( header_response[0] )

    def second_msg(self):
        request                      = urllib2.Request(self.url)
        client_first_msg        = "n=%s,r=%s" % (self.login, self.client_nonce)
        client_first_message_encoded = self.base64_no_padding( client_first_msg )
        authMsg                      = "SCRAM handshakeToken=%s, data=%s" % (self.handshake_token , client_first_message_encoded )
        request.add_header("Authorization", authMsg )

        try:
            result = urllib2.urlopen(request)
        except urlliberror2.HTTPError as e:
            header_response       = e.headers['WWW-Authenticate']
            tab_header            = header_response.split(',')
            server_data           = self.regex_after_equal( tab_header[0] )
            missing_padding = len(server_data) % 4
            if missing_padding != 0:
                server_data += '='* (4 - missing_padding)

            server_data       = b64decode( server_data  ).decode()
            tab_response      = server_data.split(',')
            server_first_msg  = server_data
            server_nonce      = self.regex_after_equal( tab_response[0] )
            server_salt       = self.regex_after_equal( tab_response[1] )
            server_iterations = self.regex_after_equal( tab_response[2] )

            if not server_nonce.startswith(self.client_nonce):
                raise Exception("Server returned an invalid nonce.")


            return ( client_first_msg, server_first_msg, server_nonce, server_salt, server_iterations )

    def get_skyspark_token(self):
        ( client_first_msg, server_first_msg, server_nonce, server_salt, server_iterations ) = self.second_msg()
        client_final_no_proof = "c=%s,r=%s" % ( standard_b64encode(b'n,,').decode() , server_nonce )
        auth_msg              = "%s,%s,%s" % ( client_first_msg, server_first_msg, client_final_no_proof )
        client_key            = hmac.new(unhexlify(self.salted_password( server_salt, server_iterations ) ), "Client Key".encode('UTF-8'), self.algorithm).hexdigest()
        stored_key            = self._hash_sha256( unhexlify(client_key) )
        client_signature      = hmac.new( unhexlify(stored_key), auth_msg.encode('utf-8'), self.algorithm ).hexdigest()
        client_proof          = self._xor (client_key, client_signature)
        client_proof_encode   = b2a_base64(unhexlify(client_proof)).decode()
        client_final          = client_final_no_proof + ",p=" + client_proof_encode
        client_final_base64   = self.base64_no_padding(client_final)
        final_msg             = "scram handshaketoken=%s,data=%s" % (self.handshake_token , client_final_base64 )
        request = urllib2.Request(self.url)
        request.add_header("Authorization", final_msg )

        auth_token = ""
        try:
            result = urllib2.urlopen(request)
            server_response = result.headers['Authentication-Info']
            tab_response = server_response.split(',')
            auth_token = self.regex_after_equal( tab_response[0] )
            print("Will use token: " + auth_token)
            return auth_token
        except urlliberror2.HTTPError as e:
            print(e.headers)

    def skyspark_request(self, url, auth_token):
        request = urllib2.Request( url )
        auth = "BEARER authToken=%s" % auth_token
        request.add_header("Authorization", auth )

        try:
            result = urllib2.urlopen(request)
            print(result.read())
        except urlliberror2.HTTPError as e:
            print(e.headers)

    def _hash_sha256(self, str):
        hashFunc = self.algorithm()
        hashFunc.update( str )
        return hashFunc.hexdigest()

    def salted_password(self, salt, iterations):
        dk = pbkdf2_hmac( self.algorithm_name, self.password.encode(), urlsafe_b64decode(salt), int(iterations))
        encrypt_password = hexlify(dk)
        return encrypt_password

    def base64_no_padding(self, s):
        encoded_str = urlsafe_b64encode(s.encode())
        encoded_str = encoded_str.decode().replace("=", "")
        return encoded_str

    def regex_after_equal(self, s):
        tmp_str = re.search( "\=(.*)$" ,s, flags=0)
        return tmp_str.group(1)

    def _xor(self, s1, s2):
        return hex(int(s1, 16) ^ int(s2, 16))[2:]

sky = SkySpark("url", "login", "password" )
auth_token = sky.get_skyspark_token()

#To call every Request Then ->
sky.skyspark_request("url/ui/apitest/about", auth_token)
