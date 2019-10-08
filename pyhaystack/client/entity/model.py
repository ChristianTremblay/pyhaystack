#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tagging Model Interface.
"""

import weakref
from .entity import Entity, DeletableEntity


class TaggingModel(object):
    """
    A base class for representing tagging models.  The tagging model
    is responsible for considering the tags present on a new entity then
    instantiating an appropriate data type based on those tags seen.
    """

    def __init__(self, session):
        """
        Initialise a new tagging model.
        """
        # Session instance
        self._session = weakref.ref(session)

        # Existing types, identified by name.
        self._types = {}

    def create_entity(self, entity_id, tags):
        """
        Create an Entity instance based on the tags present.
        """
        session = self._session()
        (class_name, types) = self._identify_types(tags)

        # Does the session instance support CRUD?  Add the appropriate base
        # class to the end of the types list.
        if hasattr(session, "delete"):
            types += [DeletableEntity]
        else:
            types += [Entity]

        try:
            class_type = self._types[class_name]
        except KeyError:
            class_type = type(class_name, tuple(types), {})
            self._types[class_name] = class_type

        entity = class_type(session, entity_id)
        entity._update_tags(tags)
        return entity

    def _identify_types(self, tags):
        """
        Inspect the tags on the to-be-created object and return a tuple
        consisting of:
        - the suggested class name
        - a list of class instances that represent the add-on types for
          that object.
        """
        raise NotImplementedError("To be implemented in %s" % self.__class__.__name__)
