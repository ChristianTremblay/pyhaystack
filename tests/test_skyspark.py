# -*- coding: utf-8 -*-
"""
Created on Wed Jun  1 22:25:49 2016

@author: CTremblay
"""

from pyhaystack.client.ops.vendor.skyspark import get_digest_info


def test_digest_creation():
    test_param = {
        "username": "alice",
        "password": "secret",
        "userSalt": "6s6Q5Rn0xZP0LPf89bNdv+65EmMUrTsey2fIhim/wKU=",
        "nonce": "3da210bdb1163d0d41d3c516314cbd6e",
    }

    test_result = get_digest_info(test_param)
    assert test_result["digest"] == "B2B3mIzE/+dqcqOJJ/ejSGXRKvE="
    assert test_result["hmac"] == "z9NILqJ3QHSG5+GlDnXsV9txjgo="
