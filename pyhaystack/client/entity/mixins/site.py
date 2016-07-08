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


    def __getitem__(self,key):
        request = self.find_entity(key)
        return request.result
      
    @property
    def equipments(self):
        try:
            return self._list_of_equip
        except AttributeError:
            request = self.find_entity('equip')
            return request.result
        
    def _add_equip(self):
        """
        Store a local copy of equip for this site
        To accelerate browser
        """
        if not '_list_of_equip' in self.__dict__.keys():
            self._list_of_equip = []       
        for equip in self['equip'].items():
            self._list_of_equip.append(equip[1])
        

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
