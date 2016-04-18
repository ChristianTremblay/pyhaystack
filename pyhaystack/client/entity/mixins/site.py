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

    def find_entity(self, filter_expr=None, single=False,
            limit=None, callback=None):
        """
        Retrieve the entities that are linked to this site.
        This is a convenience around the session find_entity method.
        """
        site_ref = hszinc.dump_scalar(self.id)
        if filter_expr is None:
            filter_expr = 'siteRef==%s' % site_ref
        else:
            filter_expr = '(siteRef==%s) and (%s)' % (site_ref, filter_expr)
        return self._session.find_entity(filter_expr, limit, single, callback)


class SiteRefMixin(object):
    """
    A mix-in used for entities that carry a 'siteRef' reference tag.
    """

    def get_site(self, callback=None):
        """
        Retrieve an instance of the site this entity is linked to.
        """
        return self._session.get_entity(self.tags['siteRef'],
                callback=callback, single=True)
