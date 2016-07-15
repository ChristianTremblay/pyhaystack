Histories
===================
Histories are a really important part of building data. Pyhaystack allows retrieving histories
as zinc grid, pandas series or pandas Dataframe depending on your needs.

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
In the following example, we will retrive all the historical value from 'today' for
all zone temperature sensors.

::

    znt = session.find_entity(filter_expr='sensor and zone and temp').result
    b = session.his_read_frame(znt, rng= 'today').result
    b

We use ``find_entity`` first, then we call ``his_read_frame`` over the result.

.. _his : http://project-haystack.org/tag/his

.. _his_read : http://project-haystack.org/doc/Ops#hisRead

.. _pandas_datastructure : http://pandas.pydata.org/pandas-docs/stable/dsintro.html