
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
          <th>S.SERVISYS.Bureau-Christian.ZN~2dT</th>
          <th>S.SERVISYS.Bureau-Matthieu.ZN~2dT</th>
          <th>S.SERVISYS.Salle-Conf~e9rence.ZN~2dT</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>2016-05-02 06:45:00.011000-04:00</th>
          <td>20.2882 °C</td>
          <td>NaN</td>
          <td>NaN</td>
        </tr>
        <tr>
          <th>2016-05-02 13:30:00.014000-04:00</th>
          <td>NaN</td>
          <td>22.365 °C</td>
          <td>NaN</td>
        </tr>
        <tr>
          <th>2016-05-02 00:00:00.015000-04:00</th>
          <td>21.0617 °C</td>
          <td>NaN</td>
          <td>NaN</td>
        </tr>
        <tr>
          <th>2016-05-02 21:15:00.010000-04:00</th>
          <td>21.2984 °C</td>
          <td>NaN</td>
          <td>NaN</td>
        </tr>
        <tr>
          <th>2016-05-02 18:15:00.072000-04:00</th>
          <td>NaN</td>
          <td>22.2423 °C</td>
          <td>NaN</td>
        </tr>
      </tbody>
    </table>
    </div>



As you can see, values in the dataframe are "objects". They are in fact
hszinc.Quantity showing a value and a unit (if any).

This mean that we will need to work to be able to make some math with
those columns sometimes.

Describe
~~~~~~~~

Describe is a Pandas function that gives you some information about a
Dataframe.

.. code:: python

    room_temp_sensors_df.describe()




.. raw:: html

    <div>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>S.SERVISYS.Bureau-Christian.ZN~2dT</th>
          <th>S.SERVISYS.Bureau-Matthieu.ZN~2dT</th>
          <th>S.SERVISYS.Salle-Conf~e9rence.ZN~2dT</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>count</th>
          <td>90</td>
          <td>90</td>
          <td>90</td>
        </tr>
        <tr>
          <th>unique</th>
          <td>90</td>
          <td>89</td>
          <td>89</td>
        </tr>
        <tr>
          <th>top</th>
          <td>22.2055 °C</td>
          <td>22.5978 °C</td>
          <td>21.7325 °C</td>
        </tr>
        <tr>
          <th>freq</th>
          <td>1</td>
          <td>2</td>
          <td>2</td>
        </tr>
      </tbody>
    </table>
    </div>



As you can see it works out of the box. But informatioin we get is not
as helpful as we would want...in fact, it's useless. Let's rework
that...

Take the first column as a Pandas Series

.. code:: python

    christian = room_temp_sensors_df['S.SERVISYS.Bureau-Christian.ZN~2dT']
    float_christian = christian.astype(float)
    float_christian.describe()




.. parsed-literal::

    count    90.000000
    mean     21.575769
    std       0.833827
    min      20.231600
    25%      20.826225
    50%      21.586100
    75%      22.315075
    max      22.745300
    Name: S.SERVISYS.Bureau-Christian.ZN~2dT, dtype: float64



This is the kind of informations useful. Are we able to do the same with
the dataframe ?

.. code:: python

    room_temp_sensors_df.astype(float).describe()




.. raw:: html

    <div>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>S.SERVISYS.Bureau-Christian.ZN~2dT</th>
          <th>S.SERVISYS.Bureau-Matthieu.ZN~2dT</th>
          <th>S.SERVISYS.Salle-Conf~e9rence.ZN~2dT</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>count</th>
          <td>90.000000</td>
          <td>90.000000</td>
          <td>90.000000</td>
        </tr>
        <tr>
          <th>mean</th>
          <td>21.575769</td>
          <td>21.769192</td>
          <td>21.159672</td>
        </tr>
        <tr>
          <th>std</th>
          <td>0.833827</td>
          <td>0.845972</td>
          <td>0.794639</td>
        </tr>
        <tr>
          <th>min</th>
          <td>20.231600</td>
          <td>20.387600</td>
          <td>19.856500</td>
        </tr>
        <tr>
          <th>25%</th>
          <td>20.826225</td>
          <td>20.875700</td>
          <td>20.364600</td>
        </tr>
        <tr>
          <th>50%</th>
          <td>21.586100</td>
          <td>22.142900</td>
          <td>21.392550</td>
        </tr>
        <tr>
          <th>75%</th>
          <td>22.315075</td>
          <td>22.545175</td>
          <td>21.799675</td>
        </tr>
        <tr>
          <th>max</th>
          <td>22.745300</td>
          <td>22.828400</td>
          <td>22.533600</td>
        </tr>
      </tbody>
    </table>
    </div>



Much better. But the problem will be the same if we want to resample
data... Pandas won't know what to do with Quantity when computing mean
or any other function...

Discussion
----------

Quantity is good, but ...
~~~~~~~~~~~~~~~~~~~~~~~~~

We need a way to "tell" Pandas how to treat Quantity values. We will
encounter problems with multistate values or binary values... This is
what I will try to figure out next.

How could we deal with units ?
------------------------------

As metadata on columns ?





.. code:: python

    float_christian.units




.. parsed-literal::

    'degC'


