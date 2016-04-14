#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
High-level Entity interface.
"""

import hszinc

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

        attrs = {
            '_session': session,
            '_entity_id': entity_id,
            '_tags': {},
            # Does the session support updates?
            '_mutable': hasattr(session, 'update') \
                and hasattr(session, 'delete')
        }

        if attrs['_mutable']:
            attrs.update({
                '_tag_updates': {},
                '_tag_deletions': set(),
                '_update_pending': False,
            })
        self.__dict__.update(attrs)

    def _update_tags(self, tags):
        """
        Update the value of given tags.
        """
        for tag, value in tags.items():
            if value is hszinc.REMOVE:
                self._tags.pop(tag, None)
            else:
                self._tags[tag] = value

    @property
    def id(self):
        """
        Return the fully qualified ID of this entity.
        """
        return hszinc.Ref(self._entity_id)

    @property
    def is_dirty(self):
        """
        Returns true if there are modifications pending submission.
        """
        if not self._mutable:
            return False
        return bool(self._tag_updates) or bool(self._tag_deletions)

    def commit(self, callback=None):
        """
        Commit any to-be-sent updates for this entity.
        """
        if not self._mutable:
            raise NotImplementedError('Server does not support updates')
        raise NotImplementedError('TODO: implement CRUD ops')

    def delete(self, callback=None):
        """
        Delete the entity.
        """
        if not self._mutable:
            raise NotImplementedError('Server does not support updates')
        raise NotImplementedError('TODO: implement CRUD ops')

    def revert(self, tags=None):
        """
        Revert the named attribute changes, or all changes.
        """
        if not self._mutable:
            # Nothing to do
            return

        if tags is None:
            self._tag_updates = {}
            self._tag_deletions = set()
        else:
            for tag in tags:
                self._tag_updates.pop(tag, None)
                self._tag_deletions.discard(tag)

    def __getattr__(self, attr):
        """
        Retrieve the value of an attribute or tag.
        """
        try:
            return self.__dict__[attr]
        except KeyError:
            pass

        # Handling of naming collisions, we shall allow tag names to be
        # prefixed with the string "tag_".  The "tag_" prefix will be stripped.
        if attr.startswith('tag_'):
            attr = attr[4:]

        tags = self.__dict__['_tags']
        if self._mutable:
            tag_updates = self.__dict__['_tag_updates']
            tag_deletions = self.__dict__['_tag_deletions']

            if attr in tag_deletions:
                # This is marked for deletion
                raise AttributeError

            try:
                return tag_updates[attr]
            except KeyError:
                pass

        try:
            return tags[attr]
        except KeyError:
            raise AttributeError

    def __setattr__(self, attr, value):
        """
        Update the value of a tag.
        """
        if attr.startswith('tag_'):
            tag = attr[4:]
        else:
            tag = attr

        if self._mutable and (tag in self._tags):
            if value is not hszinc.REMOVE:
                self._tag_updates[tag] = value
                self._tag_deletions.discard(tag)
            else:
                self._tag_updates.pop(tag, None)
                self._tag_deletions.add(tag)
            return

        super(Entity, self).__setattr__(attr, value)

    def __delattr__(self, attr):
        """
        Delete a tag.
        """
        if attr.startswith('tag_'):
            tag = attr[4:]
        else:
            tag = attr

        if self._mutable and (tag in self._tags):
            self._tag_updates.pop(tag, None)
            self._tag_deletions.add(tag)
            return

        super(Entity, self).__delattr__(attr)
