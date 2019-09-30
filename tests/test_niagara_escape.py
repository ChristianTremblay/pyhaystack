# -*- coding: utf-8 -*-
"""
First test... just import something...
"""
import pytest

from pyhaystack.client.niagara import Niagara4HaystackSession


def test_conversion_of_str():
    unescape = Niagara4HaystackSession.unescape
    dct = {
        "H.Client.Labo~2f227~2d2~2fBA~2fPC_D~e9bit_Alim": "H.Client.Labo/227-2/BA/PC_Débit_Alim"
    }
    for k, v in dct.items():
        assert unescape(k) == v
