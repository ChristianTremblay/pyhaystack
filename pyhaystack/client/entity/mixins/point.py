#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
'point' related mix-ins for high-level interface.
"""


class HisMixin(object):
    """
    A mix-in used for 'point' entities that carry the 'his' marker tag.
    """

    def his(self, rng="today", tz=None, series_format=None, callback=None):
        """
        Shortcut to read_series
        """
        return self.his_read_series(
            rng=rng, tz=tz, series_format=series_format, callback=callback
        )

    def his_read_series(self, rng, tz=None, series_format=None, callback=None):
        """
        Read the historical data of the this point and return it as a series.

        :param rng: Historical read range for the 'point'
        :param tz: Optional timezone to translate timestamps to
        :param series_format: Optional desired format for the series
        """
        return self._session.his_read_series(
            point=self, rng=rng, tz=tz, series_format=series_format, callback=callback
        )

    def his_write_series(self, series, tz=None, callback=None):
        """
        Write the historical data of this point.

        :param series: Historical series to write
        :param tz: Optional timezone to translate timestamps to
        """
        return self._session.his_write_series(
            point=self, series=series, tz=tz, callback=callback
        )


class PointMixin(object):
    @property
    def value(self):
        return (self._session.read(ids=self.id).result)[0]["curVal"]
