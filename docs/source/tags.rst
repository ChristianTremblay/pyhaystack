Tags
====
A list of tags can be found here : http://project-haystack.org/tag

For a detailed explanation of tag model, please read this : http://project-haystack.org/doc/TagModel

Pyhaystack let you find what you look for via the "find_entity" functions.

Let see how...

Finding sensors
---------------
Let say I want to find every sensors on a site which are temperature sensors used in zone.

::

    znt = session.find_entity(filter_expr='sensor and zone and temp')

This will find what you are looking for in the form of a "FindEntityOperation" object.
To use the values of this object, you will need to retrive the results using ::

    znt.result

Exploring points and tags
--------------------------

This will return a dict that can be used the way you want. As the filter may include 
a lot of points, you will need to choose the one you're interested in.

::
    
    my_office = znt['S.SERVISYS.Salle-Conf~e9rence.ZN~2dT']
    # You wil then get acces to the tags of that point
    my_office.tags

::

    {air, axAnnotated, axSlotPath='slot:/Drivers/BacnetNetwork/MSTP1/PCV$2d2$2d008/points/ZN$2dT', 
    axStatus='ok', axType='control:NumericPoint', cur, curStatus='ok', 
    curVal=BasicQuantity(23.4428, '°C'), dis='SERVISYS Salle Conférence Salle Conférence ZN-T', 
    equipRef=Ref('S.SERVISYS.Salle-Conf~e9rence', None, False), his, kind='Number', 
    navName='ZN~2dT', point, precision=1.0, sensor, siteRef=Ref('S.SERVISYS', None, False), 
    temp, tz='Montreal', unit='°C', zone}

You can access specific tags ::

    val = my_office.tags['curVal']
    # That will return BasicQuantity(23.4428, '°C')
    # from which you can retrieve
    val.value
    val.unit