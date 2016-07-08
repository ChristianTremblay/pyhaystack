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

    def get_site(self):
        print('Getting site infos...')
        sites = self._session.find_entity('site').result
        for site in sites.items():
            s = site[1]
            s._add_equip()
            self._sites.append(s)
           

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



        
    
    

