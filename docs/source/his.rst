Histories
=========

Histories are a really important part of building data. Pyhaystack allows
retrieving histories as zinc grid, pandas series or pandas Dataframe
depending on your needs.

Range
+++++

The range parameter is named ``rng`` to avoid a naming clash with the Python
``range`` keyword.  Its value can be any of the following: [ref : his_read_]

* ``"today"``
* ``"yesterday"``
* ``"first"`` (WideSky only: returns the very first record)
* ``"last"`` (WideSky only: returns the very last record)
* ``"{date}"``
* ``"{date},{date}"``
* ``"{dateTime},{dateTime}"``
* ``"{dateTime}"`` (anything after given timestamp)

As a convenience, pyhaystack also understands, and will translate a
:py:class:`datetime.date`, :py:class:`datetime.datetime` or
:py:class:`slice` object, so the following will work:

* ``datetime.date(2017, 5, 7)`` will be sent as ``"2017-05-07"``
* ``pytz.timezone('Australia/Brisbane').localize(datetime.datetime(2017,5,7,17,41))`` will be sent as ``"2017-05-07T17:41+10:00 Brisbane"``
* ``slice(datetime.date(2017, 5, 8), datetime.date(2017, 5, 10))`` will be sent as ``"2017-05-08,2017-05-10"``.

How do I generate a timestamp in a point's local time zone?
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Any Project Haystack entity that carries the ``tz`` tag when retrieved using
``find_entity`` will automatically be a sub-class of the
:py:class:`pyhaystack.client.entity.mixins.tz.TzMixin` class.

This mix-in class defines three properties:

* ``hs_tz``: The Project Haystack timezone name (equivalent to
  ``entity.tags['tz']``), e.g. ``"Brisbane"``
* ``iana_tz``: The IANA name for the timezone, e.g. ``"Australia/Brisbane"``
* ``tz``: A :py:class:`datetime.tzinfo` object that represents the
  timezone.

The timezone handling is built on the :py:mod:`pytz` module, the full documentation for which is on the `pytz website`_.

``site`` entities usually have a corresponding ``tz`` tag attached to them,
knowing this:

::

        import datetime

        # Retrieve a single entity, by ID
        op = session.get_entity('S.SERVISYS', single=True)
        op.wait()
        site = op.result        # is the entity S.SERVISYS

        # The current time at S.SERVISYS (to the microsecond)
        now = datetime.datetime.now(tz=site.tz)

        # A specific time, at S.SERVISYS
        sometime = site.tz.localize(datetime.datetime(2017, 5, 7, 18, 11))

To retrieve all historical samples between ``sometime`` and ``now``, one
could use: ::

        op = session.his_read('S.SERVISYS.Bureau-Christian.ZN~2dT',
             rng=slice(sometime, now))
        op.wait()
        history = op.result

A gotcha regarding the precision of timestamps
''''''''''''''''''''''''''''''''''''''''''''''

Some project haystack servers, notably anything that is based on
nodehaystack_ will reject timestamps that have greater than
millisecond-precision.  This may require that you round the timestamp down
to the nearest millisecond first before passing it to pyhaystack.

One way this can be done is using the following lambda function:

::

        truncate_msec = lambda dt : dt - datetime.timedelta( \
                microseconds=dt.microsecond % 1000)

which is then used like this:

::

        now_to_the_msec = truncate_msec(now)

Zinc Date and time format
+++++++++++++++++++++++++
[ref : http://project-haystack.org/doc/Zinc]

* ``<date>        := YYYY-MM-DD``
* ``<time>        := hh:mm:ss.FFFFFFFFF``
* ``<dateTime>    := YYYY-MM-DD'T'hh:mm:ss.FFFFFFFFFz zzzz``


Retrieve simple grid
--------------------

::

    op = session.his_read('S.SERVISYS.Bureau-Christian.ZN~2dT', rng='today')
    op.wait()
    op.result


Retrieve a Pandas Series
------------------------

For more details about Pandas : pandas_datastructure_

::

    op = session.his_read_series('S.SERVISYS.Bureau-Christian.ZN~2dT', rng='today')
    op.wait()
    op.result

Retrieve a Pandas Dataframe
---------------------------
In the following example, we will retrive all the historical value from 'today' for
all zone temperature sensors.

::

    # Retrieve some points
    op = session.find_entity(filter_expr='sensor and zone and temp')
    op.wait()
    znt = op.result

    # Read today's history for all found points
    op = session.his_read_frame(znt, rng= 'today')
    op.wait()
    b = op.result
    b

We use ``find_entity`` first, then we call ``his_read_frame`` over the result.


Describe
~~~~~~~~

Describe is a Pandas function that gives you some information about a
Dataframe or a serie.

Here is an example from the room_temp_serie

.. code:: python

    room_temp_serie.describe()

.. parsed-literal::

    count    55.000000
    mean     23.454680
    std       0.388645
    min      22.551900
    25%      23.169800
    50%      23.689800
    75%      23.748750
    max      23.806300
    dtype: float64

.. _his : http://project-haystack.org/tag/his

.. _his_read : http://project-haystack.org/doc/Ops#hisRead

.. _pandas_datastructure : http://pandas.pydata.org/pandas-docs/stable/dsintro.html

.. _nodehaystack : https://bitbucket.org/lynxspring/nodehaystack/issues/5/error-500-received-when-posting-zinc

.. _`pytz website` : http://pythonhosted.org/pytz/
