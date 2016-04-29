Tags
====
A list of tags can be found here : http://project-haystack.org/tag

For a detailed explanation of tag model, please read this : http://project-haystack.org/doc/TagModel

Pyhaystack let you find what you look for via the "find_entity" functions.

LEt see how...

Finding sensors
---------------
Let say I want to find every sensors on a site which are temperature sensors used in zone.

::

    znt = session.find_entity(filter_expr='sensor and zone and temp')

This will find what you are looking for ni the form of a "FindEntityOperation" object.
To use the values of this object, you will need to retrive the results using ::

    znt.result

This will return a dict that can be used the way you want.