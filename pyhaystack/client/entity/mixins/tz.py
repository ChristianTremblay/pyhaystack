#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Mix-ins for entities exposing a 'tz' tag
"""

import hszinc
import pytz


class TzMixin(object):
    """
    A mix-in used for entities that carry the 'tz' tag.
    """

    @property
    def hs_tz(self):
        """
        Return the Project Haystack timezone type.
        """
        return self.tags["tz"]

    @property
    def iana_tz(self):
        """
        Return the IANA (Olson) database timezone name.
        """
        hs_tz = self.hs_tz
        if "/" in hs_tz:
            return hs_tz  # This is the IANA zone name.

        tz_map = hszinc.zoneinfo.get_tz_map()
        return tz_map[hs_tz]

    @property
    def tz(self):
        """
        Return the timezone information (datetime.tzinfo) for this entity.
        """
        return pytz.timezone(self.iana_tz)
