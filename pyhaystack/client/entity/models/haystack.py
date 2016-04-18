#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tagging Model Interface for Project Haystack
"""

import hszinc
from ..model import TaggingModel
from ..mixins import tz, site, equip

class HaystackTaggingModel(TaggingModel):
    """
    An implementation of the Project Haystack tagging model.
    """

    def _identify_types(self, tags):
        """
        Inspect the tags on the to-be-created object and return a tuple
        consisting of:
        - the suggested class name
        - a list of class instances that represent the add-on types for
          that object.
        """
        types = []
        names = []
        if 'tz' in tags:
            # We have a timezone
            types.append(tz.TzMixin)
            names.append('Tz')

        if 'site' in tags:
            # This is a site
            types.append(site.SiteMixin)
            names.append('Site')

        if 'equip' in tags:
            # This is a site
            types.append(equip.EquipMixin)
            names.append('Equip')

        return ('%sEntity' % ''.join(sorted(names)), types)
