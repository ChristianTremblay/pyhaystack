#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
'equip' related mix-ins for high-level interface.
"""

import hszinc
from ....exception import HaystackError


class EquipMixin(object):
    """
    A mix-in used for entities that carry the 'equip' marker tag.
    """

    def find_entity(self, filter_expr=None, limit=None, single=False, callback=None):
        """
        Retrieve the entities that are linked to this equipment.
        This is a convenience around the session find_entity method.
        """
        equip_ref = hszinc.dump_scalar(self.id)
        if filter_expr is None:
            filter_expr = "equipRef==%s" % equip_ref
        else:
            filter_expr = "(equipRef==%s) and (%s)" % (equip_ref, filter_expr)
        return self._session.find_entity(filter_expr, limit, single, callback)

    def __getitem__(self, key):
        """
        In a navigation context, component of an equipment is a point (tag/entity)
        """
        # Using [key] syntax on an equipment allows to retrieve a tag directly
        # or a point referred to this particular equipment
        for each in self.tags:
            if key == each:
                return self.tags[key]
        # if key not found in tags... we probably are searching a point
        # self will call __iter__ which will look for points in equipment
        for point in self:
            # partial_results = []
            # Given an ID.... should return the point with this ID
            if key.replace("@", "") == str(point.id).replace("@", ""):
                return point
            # Given a dis or navName... should return equip
            if "dis" in each.tags:
                if key == each.tags["dis"]:
                    return each
            if "navName" in each.tags:
                if key == each.tags["navName"]:
                    return each
            if "navNameFormat" in each.tags:
                if key == each.tags["navNameFormat"]:
                    return each
        else:
            try:
                # Maybe key is a filter_expr
                request = self.find_entity(key)
                return request.result
            except HaystackError as e:
                self._session._log.warning("{} not found".format(key))

    def __iter__(self):
        """
        When iterating over an equipment, we iterate points.
        """
        for point in self.points:
            yield point

    @property
    def points(self):
        """
        First call will force reading of points and create local list
        """
        try:
            return self._list_of_points
        except AttributeError:
            print("Reading points for this equipment...")
            self._add_points()
            return self._list_of_points

    def refresh(self):
        """
        Re-create local list of equipments
        """
        self._list_of_points = []
        self._add_points()

    def _add_points(self):
        """
        Store a local copy of equip for this site
        To accelerate browser
        """
        if not "_list_of_points" in self.__dict__.keys():
            self._list_of_points = []
        for point in self["point"].items():
            self._list_of_points.append(point[1])


class EquipRefMixin(object):
    """
    A mix-in used for entities that carry an 'equipRef' reference tag.
    """

    def get_equip(self, callback=None):
        """
        Retrieve an instance of the equip this entity is linked to.
        """
        return self._session.get_entity(
            self.tags["equipRef"], callback=callback, single=True
        )
