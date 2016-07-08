#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
'equip' related mix-ins for high-level interface.
"""

import hszinc

class EquipMixin(object):
    """
    A mix-in used for entities that carry the 'equip' marker tag.
    """

    def find_entity(self, filter_expr=None, limit=None,
            single=False, callback=None):
        """
        Retrieve the entities that are linked to this equip.
        This is a convenience around the session find_entity method.
        """
        equip_ref = hszinc.dump_scalar(self.id)
        if filter_expr is None:
            filter_expr = 'equipRef==%s' % equip_ref
        else:
            filter_expr = '(equipRef==%s) and (%s)' % (equip_ref, filter_expr)
        return self._session.find_entity(filter_expr, limit, single, callback)
        
    def __getitem__(self,key):
        request = self.find_entity(key)
        return request.result
      
    @property
    def points(self):
        try:
            return self._list_of_points
        except AttributeError:
            print('Reading points...')
            self._add_points()
            return self._list_of_points
        
    def _add_points(self):
        """
        Store a local copy of equip for this site
        To accelerate browser
        """
        if not '_list_of_equip' in self.__dict__.keys():
            self._list_of_points = []       
        for equip in self['point'].items():
            self._list_of_points.append(equip[1])


class EquipRefMixin(object):
    """
    A mix-in used for entities that carry an 'equipRef' reference tag.
    """

    def get_equip(self, callback=None):
        """
        Retrieve an instance of the equip this entity is linked to.
        """
        return self._session.get_entity(self.tags['equipRef'],
                callback=callback, single=True)
