#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
'site' related mix-ins for high-level interface.
"""

import hszinc
from ....exception import HaystackError


class SiteMixin(object):
    """
    A mix-in used for entities that carry the 'site' marker tag.
    """

    def find_entity(self, filter_expr=None, single=False, limit=None, callback=None):
        """
        Retrieve the entities that are linked to this site.
        This is a convenience around the session find_entity method.
        """
        site_ref = hszinc.dump_scalar(self.id)
        if filter_expr is None:
            filter_expr = "siteRef==%s" % site_ref
        else:
            filter_expr = "(siteRef==%s) and (%s)" % (site_ref, filter_expr)
        return self._session.find_entity(filter_expr, limit, single, callback)

    def __getitem__(self, key):
        """
        A site is typically the first level object... under it there are 
        equipments (equip). 
        
        It makes sense to use site[equip] syntax to find an equip related to
        the site.
        
        But we don't want to loose the possibility to get a tag from a site
        using the same syntax.
        
        As tags are direct child of a site, they will have priority.
        """
        # First look for tags
        for each in self.tags:
            if key == each:
                return self.tags[key]
        # if key not found in tags... we probably are searching an equipment
        # self will call __iter__ which will look for equipments
        for each in self:
            # Given an ID.... should return the equip with this ID

            if key.replace("@", "") == str(each.id).replace("@", ""):
                return each
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
        When iterating over a site, we iterate equipments.
        This will allow something like :: 
            
            for equip in site:
                do something
        
        This will requires the creation of the list of equipments (see below)
        This process can be long depending on the server, this is why we 
        cache a list.
        
        It will be possible to update the list later.
        """
        for equip in self.equipments:
            yield equip

    @property
    def equipments(self):
        """
        site.equipments returns the list of equipments under a site
        
        First read will force a request and create local list
        """
        try:
            # At first, this variable will not exist... will be created
            return self._list_of_equip
        except AttributeError:
            print("Reading equipments for this site...")
            self._add_equip()
            return self._list_of_equip

    def refresh(self):
        """
        Re-create local list of equipments
        """
        self._list_of_equip = []
        self._add_equip()

    def _add_equip(self):
        """
        Store a local copy of equip names for this site
        To accelerate browser
        """
        if not "_list_of_equip" in self.__dict__.keys():
            self._list_of_equip = []
        for equip in self["equip"].items():
            self._list_of_equip.append(equip[1])


class SiteRefMixin(object):
    """
    A mix-in used for entities that carry a 'siteRef' reference tag.
    """

    def get_site(self, callback=None):
        """
        Retrieve an instance of the site this entity is linked to.
        """
        return self._session.get_entity(
            self.tags["siteRef"], callback=callback, single=True
        )
