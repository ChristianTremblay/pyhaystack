Using pyhaystack in a synchronous way
=====================================

Declaring session
-----------------

.. code:: python

    from pyhaystack.client.niagara import NiagaraHaystackSession
    import logging
    logging.root.setLevel(logging.DEBUG)
    session = NiagaraHaystackSession(uri='http://server', username='user', password='myComplicatedPassword')

Browsing a site
---------------

Let's have a look to the site

.. code:: python

    site = session.find_entity(filter_expr='site')
    site


.. parsed-literal::

    <FindEntityOperation done: {'S.SERVISYS': <@S.SERVISYS: {area=Quantity(0.0, 'ft²'), axSlotPath='slot:/site', axType='nhaystack:HSite', dis='SERVISYS', geoAddr='12', geoCity='Bromont', geoCountry='Canada', geoLat=0.0, geoLon=0.0, geoPostalCode='J2L1J5', geoState='Québec', geoStreet='Du Pacifique Est', navName='SERVISYS', navNameFormat='SERVISYS', site, tz='Montreal'}>}>


This print shows us the ``__repr__()`` function return value as a
FindEntityOperation. If we were using this asynchronously, and let say
the operation would not be finished, we would be noticed about the fact
that it's not done.

Actually, we know the operation succeeded.

But site is not an object we can use easily. To retrive something
useful, we need to call the result property.

.. code:: python

    site = site.result
    site




.. parsed-literal::

    {'S.SERVISYS': <@S.SERVISYS: {area=Quantity(0.0, 'ft²'), axSlotPath='slot:/site', axType='nhaystack:HSite', dis='SERVISYS', geoAddr='12', geoCity='Bromont', geoCountry='Canada', geoLat=0.0, geoLon=0.0, geoPostalCode='J2L1J5', geoState='Québec', geoStreet='Du Pacifique Est', navName='SERVISYS', navNameFormat='SERVISYS', site, tz='Montreal'}>}



Now we have a dict that we can use to retrieve the entity which is a
pyhaystack object

.. code:: python

    type(site['S.SERVISYS'])




.. parsed-literal::

    pyhaystack.client.entity.model.SiteTzEntity



Most common properties of entities are "dis" and "tags"

.. code:: python

    site['S.SERVISYS'].dis




.. parsed-literal::

    'SERVISYS'



.. code:: python

    site['S.SERVISYS'].tags




.. parsed-literal::

    {area=Quantity(0.0, 'ft²'), axSlotPath='slot:/site', axType='nhaystack:HSite', dis='SERVISYS', geoAddr='12', geoCity='Bromont', geoCountry='Canada', geoLat=0.0, geoLon=0.0, geoPostalCode='J2L1J5', geoState='Québec', geoStreet='Du Pacifique Est', navName='SERVISYS', navNameFormat='SERVISYS', site, tz='Montreal'}



.. code:: python

    site['S.SERVISYS'].tags['tz']




.. parsed-literal::

    'Montreal'



Wrap up
-------

We created a request to find something on the server (the site).
Pyhaystack gave us in return an operation. This operation runs in the
background (if you're using an asynchronous call or a thread...) The
operation tells you when it's done.

When the operation is done, you can retrieve the "result" using the
property named "result".

Typically, result will give a dict that contains the information you
need.

In our case, the result was a pyhaystack entity that contained tags.

Tags are also a dict that can be browsed using square brackets.

Histories
---------

Histories are a big parts of pyhaystack if you're using it for numerical
analysis.

Pyhaystack provides functions to retrieve histories from your site
allowing you to get your result in the form you want it (simple grid,
Pandas Series or Pandas Dataframe).

As we want to do numerical analysis, I'll focus on Pandas Series and
Dataframe.

Find histories
~~~~~~~~~~~~~~

As we saw earlier, we can retrieve entities using pyhaystack. Those
entities can be used to retrieve histories.

Let's say we would want to retrieve every room temperature sensors on
site.

.. code:: python

    room_temp_sensors = session.find_entity(filter_expr='sensor and zone and temp').result
    room_temp_sensors_df = session.his_read_frame(room_temp_sensors, rng= 'today').result
    room_temp_sensors_df.tail()




.. raw:: html

    <div>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>S.SERVISYS.Corridor.ZN~2dT</th>
          <th>S.SERVISYS.Bureau-Christian.ZN~2dT</th>
          <th>S.SERVISYS.R~e9ception.ZN~2dT</th>
          <th>S.SERVISYS.Bureau-Matthieu.ZN~2dT</th>
          <th>S.SERVISYS.Bureau-Patrick.ZN~2dT</th>
          <th>S.SERVISYS.Bureau-Marc.ZN~2dT</th>
          <th>S.SERVISYS.Salle-Conf~e9rence.ZN~2dT</th>
          <th>S.SERVISYS.Bureau-Philippe.ZN~2dT</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>2016-06-29 13:15:00.598000-04:00</th>
          <td>NaN</td>
          <td>NaN</td>
          <td>NaN</td>
          <td>NaN</td>
          <td>21.7276</td>
          <td>NaN</td>
          <td>NaN</td>
          <td>NaN</td>
        </tr>
        <tr>
          <th>2016-06-29 13:15:00.791000-04:00</th>
          <td>NaN</td>
          <td>NaN</td>
          <td>NaN</td>
          <td>NaN</td>
          <td>NaN</td>
          <td>21.6487</td>
          <td>NaN</td>
          <td>NaN</td>
        </tr>
        <tr>
          <th>2016-06-29 13:15:00.943000-04:00</th>
          <td>NaN</td>
          <td>NaN</td>
          <td>23.3938</td>
          <td>NaN</td>
          <td>NaN</td>
          <td>NaN</td>
          <td>NaN</td>
          <td>NaN</td>
        </tr>
        <tr>
          <th>2016-06-29 13:15:01.158000-04:00</th>
          <td>NaN</td>
          <td>NaN</td>
          <td>NaN</td>
          <td>NaN</td>
          <td>NaN</td>
          <td>NaN</td>
          <td>NaN</td>
          <td>23.089</td>
        </tr>
        <tr>
          <th>2016-06-29 13:15:01.609000-04:00</th>
          <td>22.8838</td>
          <td>NaN</td>
          <td>NaN</td>
          <td>NaN</td>
          <td>NaN</td>
          <td>NaN</td>
          <td>NaN</td>
          <td>NaN</td>
        </tr>
      </tbody>
    </table>
    </div>



It's also possible to get a serie out of a sensor : 

.. code:: python

    room_temp = session.find_entity(filter_expr='sensor and zone and temp').result
    room_temp_serie = session.his_read_series(room_temp['S.SERVISYS.Corridor.ZN~2dT'], rng= 'today').result
    room_temp_serie

.. parsed-literal::

    2016-06-29 00:00:01.937000-04:00    23.8063
    2016-06-29 00:15:01.510000-04:00    23.8011
    2016-06-29 00:30:01.599000-04:00    23.8020
    2016-06-29 00:45:01.931000-04:00    23.7959
    2016-06-29 01:00:03.847000-04:00    23.7961
    2016-06-29 01:15:01.486000-04:00    23.7956
    2016-06-29 01:30:01.884000-04:00    23.7946
    2016-06-29 01:45:01.663000-04:00    23.7944
    2016-06-29 02:00:01.820000-04:00    23.7932
    2016-06-29 02:15:01.766000-04:00    23.7929
    2016-06-29 02:30:01.587000-04:00    23.7854
    2016-06-29 02:45:01.413000-04:00    23.7606
    2016-06-29 03:00:02.369000-04:00    23.7487
    2016-06-29 03:15:01.584000-04:00    23.7490
    2016-06-29 03:30:02.019000-04:00    23.7488
    2016-06-29 03:45:01.478000-04:00    23.7474
    2016-06-29 04:00:01.638000-04:00    23.7467
    2016-06-29 04:15:01.756000-04:00    23.7450
    2016-06-29 04:30:01.865000-04:00    23.7450
    2016-06-29 04:45:01.782000-04:00    23.7254
    2016-06-29 05:00:01.586000-04:00    23.7142
    2016-06-29 05:15:01.370000-04:00    23.6986
    2016-06-29 05:30:01.931000-04:00    23.6977
    2016-06-29 05:45:01.758000-04:00    23.6969
    2016-06-29 06:00:01.920000-04:00    23.6954
    2016-06-29 06:15:01.498000-04:00    23.6922
    2016-06-29 06:30:01.810000-04:00    23.6946
    2016-06-29 06:45:00.236000-04:00    23.6898
    2016-06-29 07:00:01.763000-04:00    23.6569
    2016-06-29 07:15:01.751000-04:00    23.6571
    2016-06-29 07:30:01.604000-04:00    23.6137
    2016-06-29 07:45:01.762000-04:00    23.6046
    2016-06-29 08:00:02.015000-04:00    22.9552
    2016-06-29 08:15:01.482000-04:00    22.6888
    2016-06-29 08:30:01.687000-04:00    22.9885
    2016-06-29 08:45:00.155000-04:00    23.2589
    2016-06-29 09:00:02.063000-04:00    23.4131
    2016-06-29 09:15:01.586000-04:00    22.8142
    2016-06-29 09:30:01.694000-04:00    22.5519
    2016-06-29 09:45:01.475000-04:00    22.9732
    2016-06-29 10:00:01.994000-04:00    23.2174
    2016-06-29 10:15:01.652000-04:00    23.4262
    2016-06-29 10:30:01.596000-04:00    23.4417
    2016-06-29 10:45:01.891000-04:00    22.8423
    2016-06-29 11:00:01.873000-04:00    22.7915
    2016-06-29 11:15:01.775000-04:00    23.1458
    2016-06-29 11:30:01.641000-04:00    23.4154
    2016-06-29 11:45:01.652000-04:00    23.6271
    2016-06-29 12:00:02.147000-04:00    22.9879
    2016-06-29 12:15:01.527000-04:00    22.6588
    2016-06-29 12:30:01.819000-04:00    22.8726
    2016-06-29 12:45:01.590000-04:00    23.1938
    2016-06-29 13:00:01.880000-04:00    23.4289
    2016-06-29 13:15:01.609000-04:00    22.8838
    2016-06-29 13:30:00.607000-04:00    22.8446
    dtype: float64

As seen when we covered Quantities, you can extract metadata from Series and
get the unit.

.. code:: python

    room_temp_serie.meta['units']

.. parsed-literal::

    <UnitsContainer({'degC': 1.0})>

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



