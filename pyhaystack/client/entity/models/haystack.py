#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tagging Model Interface for Project Haystack
"""

import hszinc
from ..model import TaggingModel
from ..mixins import tz, site, equip, point


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
        if "tz" in tags:
            # We have a timezone
            types.append(tz.TzMixin)
            names.append("Tz")

        if "site" in tags:
            # This is a site
            types.append(site.SiteMixin)
            names.append("Site")
        elif "siteRef" in tags:
            # This links to a site
            types.append(site.SiteRefMixin)
            names.append("SiteRef")

        if "equip" in tags:
            # This is a site
            types.append(equip.EquipMixin)
            names.append("Equip")
        elif "equipRef" in tags:
            # This links to an equip
            types.append(equip.EquipRefMixin)
            names.append("EquipRef")

        if "point" in tags:
            types.append(point.PointMixin)
            if "his" in tags:
                types.append(point.HisMixin)
                names.append("His")

        return ("%sEntity" % "".join(sorted(names)), types)
