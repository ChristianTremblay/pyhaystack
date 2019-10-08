#!python
# -*- coding: utf-8 -*-
"""
Niagara makes some weird thing with encoding.

"""

import re


class EncodingMixin(object):
    """
    This will add functions needed to decode characters coming
    from Niagara in its weird format ~2d like

    """

    @classmethod
    def unescape(self, s):
        """
        Niagara and nhaystack will spit out ~xy characters
        Those are in fact unicode and can be escaped to be
        easier to read

        "H.Client.Labo~2f222~2dBA~2fPC_D~e9bit_Alim"
        becomes
        "H.Client.Labo/222-BA/PC_Débit_Alim"
        """
        _s = s
        escape = re.compile(r"~(\w\w)")
        for each in escape.finditer(_s):
            _s = re.sub(each.group(0), chr(int(each.group(1), base=16)), _s)
        return _s
