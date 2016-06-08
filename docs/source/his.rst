Histories
===================
Histories (trend) are accessible using 
`his_read_series(self, point, rng, tz=None,series_format=None, callback=None)` function.

::

    session.his_read('S.SERVISYS.Bureau-Christian.ZN~2dT', rng='today').result

Histories can be retrive as a zinc grid, Pandas series or Pandas Dataframe.

Range
+++++
rng (range) can be one of the following 
[ref : his_read_]

* "today"
* "yesterday"
* "{date}"
* "{date},{date}"
* "{dateTime},{dateTime}"
* "{dateTime}" // anything after given timestamp

Zinc Date and time format
+++++++++++++++++++++++++
[ref : http://project-haystack.org/doc/Zinc]

* <date>        := YYYY-MM-DD
* <time>        := hh:mm:ss.FFFFFFFFF
* <dateTime>    := YYYY-MM-DD'T'hh:mm:ss.FFFFFFFFFz zzzz


Retrieve simple grid
--------------------
::
    
    session.his_read('S.SERVISYS.Bureau-Christian.ZN~2dT', rng='today').result



Retrieve a Pandas Series
------------------------
For more details about Pandas : pandas_datastructure_
::

    session.his_read_series('S.SERVISYS.Bureau-Christian.ZN~2dT', rng= 'today').result

Retrieve a Pandas Dataframe
---------------------------
::

    znt = session.find_entity(filter_expr='sensor and zone and temp').result
    b = session.his_read_frame(znt, rng= 'today').result
    b

will return a dataframe of all entities history

.. _his : http://project-haystack.org/tag/his

.. _his_read : http://project-haystack.org/doc/Ops#hisRead

.. _pandas_datastructure : http://pandas.pydata.org/pandas-docs/stable/dsintro.html