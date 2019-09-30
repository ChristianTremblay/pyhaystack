# -*- coding: utf-8 -*-
"""
First test... just import something...
"""
import pytest
import sys

from pyhaystack.client.niagara import Niagara4HaystackSession


@pytest.mark.skipif(sys.version_info < (3, 4), reason="requires python3 or higher")
def test_conversion_of_str():
    unescape = Niagara4HaystackSession.unescape
    dct = {
        "H.Client.Labo~2f227~2d2~2fBA~2fPC_D~e9bit_Alim": "H.Client.Labo/227-2/BA/PC_Débit_Alim"
    }
    for k, v in dct.items():
        assert unescape(k) == v
