#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
'site' related mix-ins for high-level interface.
"""

import hszinc

class SiteMixin(object):
    """
    A mix-in used for entities that carry the 'site' marker tag.
    """

    def find_entity(self, filter_expr, limit=None, callback=None):
        """
        Retrieve the entities that are linked to this site.
        This is a convenience around the session find_entity method.
        """
        return self._session.find_entity(
                '(%s) and (siteRef==%s)' % (filter_expr, \
                        hszinc.dump_scalar(self.id)), limit, callback)
