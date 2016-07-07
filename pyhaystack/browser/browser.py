# -*- coding: utf-8 -*-

class Browser(object):
    """
    This class will provide helper function to browse haystack site
    """
    _session = None
    
    def __init__(self, session):
        Browser._session = session
        self._sites = []
        self.get_site()
        self.get_equip()



    def get_site(self):
        print('Getting site infos...')
        sites = self._session.find_entity('site').result
        for site in sites.items():
            self._sites.append(Site(site[1]))
        
    def get_equip(self):
        print('Getting equip infos...')
        equips = self._session.find_entity('equip').result
        temp = []        
        for equip in equips.items():
            temp.append(Equipment(equip[1]))
        # Then class them in the right site
        for equip in temp:
            ref = equip.parent.name.split('.')[1]
            self[ref].add_equip(equip)
            

    @property
    def sites(self):
        return list([site for site in self._sites])
          
    def __getitem__(self,key):
        """
        Will return a site
        """
        for each in self._sites:
            if each.dis == key:
                return each



class HEntity(object):
    def __init__(self, entity):
        self._tags = entity.tags
        self._class = entity
        self.name = self._class.dis
        
    def __getitem__(self, key):
        return self._tags[key]
    
    @property
    def parent(self):
        raise NotImplementedError()
        
    @property
    def dis(self):
        return self._class.dis
    
    @property
    def tags(self):
        return list([key for key in self._tags.keys()])

    @property
    def infos(self):
        return list([('%s : %s') % (key, value) for key, value in self._tags.items()])    
    
    def __repr__(self):
        return ('%s, %s' % (type(self._class), self.name))


class Site(HEntity):
    def __init__(self, site):
        self._equipments = []
        super(Site, self).__init__(site)
        
    def add_equip(self, equip):
        self._equipments.append(equip)
      
    @property
    def parent(self):
        return "Site doesn't have parent"
        
    @property
    def equip(self):
        return list([equip for equip in self._equipments])
        
    def __getitem__(self, key):
        for each in self._equipments:
            if each.dis == key:
                return each
        raise KeyError('Item not found')
        
class Equipment(HEntity):
    def __init__(self, equip):
        self.points = []
        super(Equipment, self).__init__(equip)
        self.add_points()
    
    @property
    def parent(self):
        return self._tags['siteRef']
        
    def add_points(self):
        """
        Fill equipment with its points
        """
        # In Niagara, navName is the real name of the equip. Dis is made from
        # Site AND Equip name
        if 'navName' in self.tags:
            name = self._tags['navName']
        else:
            name = self.dis
        points = Browser._session.find_entity('equipRef==@%s.%s' % (self.parent.name, name)).result
        for point in points.items():
            self.points.append(Point(point[1]))
            
#    def __getitem__(self, key):
#        if 'navName' in self.tags:
#            name = self._tags['navName']
#        else:
#            name = self.dis

        
class Point(HEntity):
    def __init__(self, equip):
        super(Point, self).__init__(equip)
    
    @property
    def parent(self):
        return self._tags['equipRef']
        
    @property
    def value(self):
        return self._tags['curVal']

            
    
    

