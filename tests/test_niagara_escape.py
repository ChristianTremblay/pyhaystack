# -*- coding: utf-8 -*-
"""
First test... just import something...
"""
import pytest

from pyhaystack.util.tools import niagara_unescape

def test_conversion_of_str():
    dct = {"H.Client.Labo~2f227~2d2~2fBA~2fPC_D~e9bit_Alim" : "H.Client.Labo/227-2/BA/PC_Débit_Alim"} 
    for k, v in dct.items():
        assert niagara_unescape(k) == v
    
