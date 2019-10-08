#!python
# -*- coding: utf-8 -*-

from binascii import b2a_hex, unhexlify, b2a_base64, hexlify
from requests.auth import HTTPBasicAuth
from base64 import standard_b64encode, b64decode, urlsafe_b64encode, urlsafe_b64decode
from hashlib import sha1, sha256

try:
    # Python 3.4+
    from hashlib import pbkdf2_hmac
except ImportError:
    # Python 3.3 and earlier, needs backports-hashlib.pbkdf2
    # https://pypi.python.org/pypi/backports.pbkdf2/
    from backports.pbkdf2 import pbkdf2_hmac

import re
import os


def get_nonce():
    return b2a_hex(os.urandom(32)).decode()


def get_nonce_16():
    return urlsafe_b64encode(os.urandom(16)).decode()


def _hash_sha256(client_key, algorithm):
    hashFunc = algorithm()
    hashFunc.update(client_key)
    return hashFunc.hexdigest()


def salted_password(salt, iterations, algorithm_name, password):
    dk = pbkdf2_hmac(
        algorithm_name, password.encode(), urlsafe_b64decode(salt), int(iterations)
    )
    encrypt_password = hexlify(dk)
    return encrypt_password


def salted_password_2(salt, iterations, algorithm_name, password):
    dk = pbkdf2_hmac(
        algorithm_name, password.encode(), unhexlify(salt), int(iterations)
    )
    encrypt_password = hexlify(dk)
    return encrypt_password


def base64_no_padding(s):
    encoded_str = urlsafe_b64encode(s.encode())
    encoded_str = encoded_str.decode().replace("=", "")
    return encoded_str


def regex_after_equal(s):
    tmp_str = re.search("\=(.*)$", s, flags=0)
    return tmp_str.group(1)


def _xor(s1, s2):
    return hex(int(s1, 16) ^ int(s2, 16))[2:]
