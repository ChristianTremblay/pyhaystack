# -*- coding: utf-8 -*-
"""
Created on Sat Jan 23 20:57:16 2016

@author: CTremblay, sjlongland
"""

from ...history.HisRecord import HisRecord

import hszinc
import time

class HistoriesMixin(object):
    """
    This class holds every functions related to histories that apply to
    HaystackClient
    """
    def hisRead(self, **kwargs):
        """
        This method returns a list of history records
        arguments are :
        ids : a ID or a list of ID
        AND_search : a list of keywords to look for in trend names
        OR_search : a list of keywords to look for in trend names
        rng : haystack range (today, yesterday, last24hours...
        start : string representation of start time ex. '2014-01-01T00:00'
        end : string representation of end time ex. '2014-01-01T00:00'
        """
        self._filteredList = [] # Empty list to be returned
        log = self._log.getChild('his_read')
        # Keyword Arguments
        log.debug('Keywords: %s', kwargs)
        ids = kwargs.pop('id','')
        AND_search = kwargs.pop('AND_search','')
        OR_search = kwargs.pop('OR_search','')
        rng = kwargs.pop('rng',None)
        start = kwargs.pop('start',None)
        end = kwargs.pop('end',None)
        takeall = kwargs.pop('all','')
        # Remaining kwargs...
        if kwargs: raise TypeError('Unknown argument(s) : %s' % kwargs)

        # Build datetimeRange based on start and end
        if (start is not None) and (end is not None):
            if rng is not None:
                raise ValueError('rng and start/end are mutually exclusive')
            datetimeRange = (start, end)
        elif rng is not None:
            datetimeRange = rng
        else:
            raise ValueError('start and end or rng is required')


        # Find histories matching ALL keywords in AND_search
        for eachHistory in self.hisAll():
            takeit = False
            # Find histories matching ANY keywords in OR_search
            if (AND_search != '') and all([keywords in eachHistory['name'] for keywords in AND_search]):
                log.debug('AND_search : Adding %s to recordList',
                    eachHistory['name'])
                takeit = True

            # Find histories matching ANY ID in id list
            elif (OR_search != '') and any([keywords in eachHistory['name'] for keywords in OR_search]):
                log.debug('OR_search : Adding %s to recordList',
                    eachHistory['name'])
                takeit = True

            elif (ids != '') and any([id in eachHistory['id'] for id in ids]):
                log.debug('ID found : Adding %s to recordList',
                        eachHistory['name'])
                takeit = True

            elif takeall != '':
                log.debug('Adding %s to recordList', eachHistory['name'])
                takeit = True

            if takeit:
                self._filteredList.append(HisRecord(self, eachHistory['id'],datetimeRange))


        log.debug('%d trends found', len(self._filteredList))
        return self._filteredList

    def hisWrite(self, records):
        '''
        Write one or more records to one or more entities.

        records may be:
        - a list of dicts
        - a single dict (for a single record)

        the dicts take the form:
        - a key named 'ts' with a datetime object
        - IDs and the sample values in key-value pairs.
        '''
        if isinstance(records, dict):
            records = [records]

        # Get a list of all points being written to.
        points = set()
        for r in records:
            points.update(set(r.keys()) - set(['ts']))

        # Get the timezones needed for each point
        tz = dict([
            (point, hszinc.zoneinfo.timezone(self.getHistMeta(point)['tz']))
            for point in points
        ])

        if len(points) == 1:
            # Single point hist-write.
            point_id = list(points)[0]
            tz = tz[point_id]
            grid = hszinc.Grid()
            grid.metadata['id'] = hszinc.Ref(point_id)
            grid.column['ts'] = {}
            grid.column['val'] = {}
            for r in records:
                ts = r['ts']
                value = r[point_id]

                # Localise timestamp
                if ts.tzinfo is None:
                    ts = tz.localize(ts)
                else:
                    ts = ts.astimezone(tz)

                grid.append({'ts': ts, 'val': value})
        else:
            # Multi-point hist-write.
            grid = hszinc.Grid()
            grid.metadata['id'] = hszinc.Ref(point_id)
            grid.column['ts'] = {}
            grid_cols = {}
            for num, point in zip(range(0, len(points)), points):
                col = 'v%d' % num
                grid_cols[point] = col
                grid.column[col] = {'id': hszinc.Ref(point)}

            for r in records:
                ts = r['ts']
                row = {}

                for point, col in grid_cols.items():
                    if 'ts' not in row:
                        # Localise timestamp
                        if ts.tzinfo is None:
                            row['ts'] = tz[point].localize(ts)
                        else:
                            row['ts'] = ts.astimezone(tz[point])
                    row[col] = r.get(point)
                grid.append(row)

        self._post_grid('hisWrite', grid)

    def refreshHisList(self, force_refresh=False):
        """
        This function retrieves every histories in the server and returns a
        list of id
        """
        if (self._history_expiry > time.time()) and (not force_refresh):
            return

        history = {}
        for pt in self._get_grid('read', filter='his'):
            pt_id = pt.pop('id')
            if pt_id.has_value:
                pt['name'] = pt_id.value
            history[pt_id.name] = pt
        self._history = history
        self._history_expiry = time.time() + 300.0  # TODO: make configurable

    def hisAll(self):
        """
        Returns all history names and id
        """
        self.refreshHisList()
        return [
                {'id': his_id, 'name': his_meta.get('navName')} \
                        for his_id, his_meta in
                        self._history.items()
        ]

    def getHistMeta(self, hist_id):
        '''
        Get the metadata for a given historical data point.  Raises KeyError
        if the item does not exist.
        '''
        self.refreshHisList()
        return self._history[hist_id]