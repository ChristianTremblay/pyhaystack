Using pyhaystack in a synchronous way
=====================================
Exploring a site is the first thing we do to start analysing it. Here are some
tips on the way you can explore your site.

We assume here that the session is created and you defined ::

    site = session.site

Browsing a site
---------------
A site is typically filled with equipments. Pyhaystack assumes that if you use
bracket request over a site, you probably want to explore :

    * tags (area, dis, geoAddr, tz, etc...)
    * equipments (VAV, AHU, etc...)
    * anything else

Lookup will be made in this order. If the key you passed can't be found in tags,
pyhaystack will start building a list of equipments under the site.

Read tags
++++++++++
All tags can be retrieved using site['tagName']::

    site ['area']

    # Returns
    BasicQuantity(0.0, 'ft²')

Find equipments
++++++++++++++++
Equipments can be found using the same syntax.
So if you write ::

    my_equip = site['myEquip']
    Reading equipments for this site...

If the equipment exist, it will be returned

Once the first read is done, you can access the list using ::

    site.equipments
    # Returns a list of EquipSiteRefEntity

.. note::
    The key provided will be compared to the ID, the dis and the navName. And
    will return the first hit.

Find points under equipments
+++++++++++++++++++++++++++++
The same logic we saw for site can be applied to equipment. Equipments are typically
filled with points that we need to access to. Using the bracket syntax should
allow us to do so.
So if you write ::

    zone_temp = my_equip['ZN~2dT']
    Reading points for this equipment...

.. note::
    This time again, a list is populated under the object. All points for the
    equipment will be accessible using the simple syntax `equip.points`. This
    list is also used to iterate rapidly over point when making search. This way,
    pyhaystack doesn't need to poll the server.

Finding something else using a filter
++++++++++++++++++++++++++++++++++++++
If the square bracket search doesn't find tag or equipment or point, it will also
try to use find_entity  using the provided key. This way, you can also use this
simple syntax to look for more complicated results ::

    air_sensors = my_equip['sensor and air']
    # Returns all the points corresponding to this search.

.. note::
    The square bracket search is context sensitive. The find_entity function
    will be called "where the search is done". This means that when using this
    search under an equipment, it will look under the equipment. You can also
    use this search under a site, the search will be done under this particular
    site.

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

Points history
~~~~~~~~~~~~~~
When using the square bracket search to retrieve a point, you can also chain
the his function to the result ::

    pcv6 = site['PCV~2d11~2d012_BVV~2d06']
    zone_temp = pcv6['ZN~2dT']
    zone_temp.his()

    # Return a Pandas Series with today's history by default.

Refer to the chapter on histories for more details.






