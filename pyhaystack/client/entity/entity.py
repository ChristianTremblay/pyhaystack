#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
High-level Entity interface.
"""

from hszinc import Ref
from .tags import ReadOnlyEntityTags, MutableEntityTags


class Entity(object):
    """
    A base class for Project Haystack entities.  This is a base class that is
    then combined with mix-ins depending on the tags present for the entity and
    the tagging model in use (by default, we use the "Project Haystack" tagging
    model, but others such as ISA-95 may exist).

    This base class just exposes the tags, and if supported by the server, may
    expose the ability to update those tags.
    """

    def __init__(self, session, entity_id):
        """
        Initialise a new high-level entity object.

        :param session: The connection session object.
        :param entity_id: The entity's fully qualified ID.
        """

        self._session = session
        self._entity_id = entity_id

        if hasattr(session, "update"):
            tags = MutableEntityTags(self)
        else:
            tags = ReadOnlyEntityTags(self)

        self._tags = tags
        self._valid = True

    @property
    def id(self):
        """
        Return the fully qualified ID of this entity.
        """
        return Ref(self._entity_id)

    @property
    def dis(self):
        """
        Return the description field of the entity.
        """
        return self._tags["dis"]

    @property
    def tags(self):
        """
        Return the tags of this entity.
        """
        return self._tags

    def __repr__(self):
        """
        Return a string representation of the entity.
        """
        return "<%s: %s>" % (self.id, self.tags)

    def _update_tags(self, tags):
        """
        Update the value of given tags.
        """
        self._tags._update_tags(tags)
        if hasattr(self._session, "_check_entity_type") and (
            not self._session._check_entity_type(self)
        ):
            self._invalidate()

    def _invalidate(self):
        """
        Mark this instance of the entity as invalid, ensure it does not exist
        in cache.
        """
        if self._session._entities.get(self._entity_id) is self:
            self._session._entities.pop(self._entity_id, None)
        self._valid = False


class DeletableEntity(Entity):
    """
    Class to represent entities that can be deleted from the Haystack server
    (the server implements the 'delete' operation).
    """

    def delete(self, callback=None):
        """
        Delete the entity.
        """
        if not self._valid:
            raise StaleEntityInstanceError()
        raise NotImplementedError("TODO: implement CRUD ops")


class StaleEntityInstanceError(Exception):
    """
    Exception thrown when an entity instance is "stale", that is, the
    entity class type no longer matches the tag set present in the entity.
    """

    pass
