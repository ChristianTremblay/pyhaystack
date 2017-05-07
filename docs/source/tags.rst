Tags
====

A list of tags can be found here : http://project-haystack.org/tag

For a detailed explanation of tag model, please read this:
http://project-haystack.org/doc/TagModel

Pyhaystack let you find what you look for via the "find_entity" functions.

Let see how...

Finding sensors
---------------
Let say I want to find every sensors on a site which are temperature sensors used in zone.

::

    op = session.find_entity(filter_expr='sensor and zone and temp')
    op.wait()

This will find what you are looking for in the form of a "FindEntityOperation" object.
To use the values of this object, you will need to retrive the results using ::

    znt = op.result

Exploring points and tags
--------------------------

This will return a `dict` object that contains all of the Project Haystack
entities that matched the given filter string.  The entities are keyed by
identifier.  When exploring interactively, you can get a list of all the
matching entities' identifiers by calling:

::
    list(znt.keys())

To retrieve a specific entity, you give its identifier as the key:

::

    my_office = znt['S.SERVISYS.Salle-Conf~e9rence.ZN~2dT']

Having done this, it is possible to interrogate the tags attached to this
entity.  These are accessed by the `tags` property, which also returns a
:py:class:`pyhaystack.cient.entity.tags.MutableEntityTags` if your server
supports making changes via the Project Haystack API (currently only WideSky),
or :py:class:`pyhaystack.cient.entity.tags.ReadOnlyEntityTags` otherwise.

Both classes function like a `dict`.

::
    my_office.tags

    {air, axAnnotated,
      axSlotPath='slot:/Drivers/BacnetNetwork/MSTP1/PCV$2d2$2d008/points/ZN$2dT',
      axStatus='ok', axType='control:NumericPoint', cur, curStatus='ok',
      curVal=BasicQuantity(23.4428, '°C'),
      dis='SERVISYS Salle Conférence Salle Conférence ZN-T',
      equipRef=Ref('S.SERVISYS.Salle-Conf~e9rence', None, False),
      his, kind='Number', navName='ZN~2dT', point,
      precision=1.0, sensor, siteRef=Ref('S.SERVISYS', None, False),
      temp, tz='Montreal', unit='°C', zone}

You can access specific tags, again, by giving the tag's name as the key ::

    val = my_office.tags['curVal']
    # That will return BasicQuantity(23.4428, '°C')
    # from which you can retrieve
    val.value
    val.unit

What is the `~nn` codes I keep seeing?
''''''''''''''''''''''''''''''''''''''

This is a feature specific to nHaystack.  Project Haystack entity identifiers
have a restricted character set, and only support a small subset of possible
ASCII characters.  nHaystack derives the entity's identifier from the name
supplied by the user in the back-end configuration.

To encode other forms of characters (from the ISO8859-1 character set), the
character is replaced by the sequence, `~nn` where `nn` is the hexadecimal
character code for that character.  In this case, you'll see `~2d` in place of
`-`, and `~e9` in place of `é`.

Adding, Changing and Deleting tags
----------------------------------

From this interface, it is also possible to update the values of these tags.
This requires a back-end server that supports "CRUD" operations (Create, Read,
Update & Delete).  If your server supports these operations (and pyhaystack
supports using them), the `tags` property will be of type
:py:class:`pyhaystack.cient.entity.tags.MutableEntityTags`.

Again, this object functions like a `dict`:

::
        # Change the display text
        znt.tags['dis'] = 'A new display text string'

        # Delete the 'his' tag
        del znt.tags['his']

        # Add a new tag
        znt.tags['space'] = hszinc.Quantity(4, 'm²')

The changes are held in memory until such time as you either commit them, or
revert them.  When changes are stored locally, the `is_dirty` property will
return `True`.

To forget these changes and roll it back to what's live on the server, call
`revert`.  This can take an optional list (or other iterable sequence) of tag
names that you specifically wish to revert.

Alternatively, to push these changes, call `commit`, which takes an optional
callback function.  The return value of `commit` is a state machine that
returns an instance of the updated entity on success (or raises an exception
with the error):

::
        op = znt.commit()
        op.wait()

        assert op.result is znt # ← this assert will pass
