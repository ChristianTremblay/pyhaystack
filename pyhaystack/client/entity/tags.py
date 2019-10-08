#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Entity tag interface.  This file implements the interfaces that will be used
to access and store tags of an entity.
"""

import hszinc

try:
    import collections.abc as col
except ImportError:
    import collections as col
import weakref
from ...util.asyncexc import AsynchronousException
from .ops.crud import EntityTagUpdateOperation


class BaseEntityTags(object):
    """
    A base class for storing entity tags.
    """

    def __init__(self, entity):
        """
        Initialise a new high-level entity tag storage object.

        :param session: The connection session object.
        :param entity_id: The entity's fully qualified ID.
        """

        self._entity = weakref.ref(entity)
        self._tags = {}

    def __repr__(self):
        """
        Dump a string representation of the tags.
        """

        def _dump_tag(ti):
            (t, v) = ti
            if v is hszinc.MARKER:
                return t
            elif v is hszinc.REMOVE:
                return "R(%s)" % t
            else:
                return "%s=%r" % (t, v)

        tags = list(map(_dump_tag, self.items()))
        tags.sort()
        return "{%s}" % ", ".join(tags)

    def __iter__(self):
        """
        Iterate over the tags present.
        """
        return iter(self._tags)

    def __len__(self):
        """
        Return the number of tags present.
        """
        return len(self._tags)

    def __getitem__(self, tag):
        """
        Return the value of a tag.
        """
        return self._tags[tag]

    def _update_tags(self, tags):
        """
        Update the value of given tags.
        """
        stale = set(self._tags.keys())
        for tag, value in tags.items():
            # The "absence" of tags is not obvious
            if (value is hszinc.REMOVE) or (value is None):
                continue
            else:
                self._tags[tag] = value
                stale.discard(tag)

        for tag in stale:
            self._tags.pop(tag, None)


class BaseMutableEntityTags(BaseEntityTags):
    """
    A base class for entity tags that supports modifications to the tag set.
    """

    _ENTITY_TAG_UPDATE_OPERATION = EntityTagUpdateOperation

    def __init__(self, entity):
        super(BaseMutableEntityTags, self).__init__(entity)
        self._tag_updates = {}
        self._tag_deletions = set()

    @property
    def is_dirty(self):
        """
        Returns true if there are modifications pending submission.
        """
        return bool(self._tag_updates) or bool(self._tag_deletions)

    def commit(self, callback=None):
        """
        Commit any to-be-sent updates for this entity.
        """
        entity = self._entity()
        updates = self._tag_updates.copy()
        updates["id"] = entity.id
        for tag in self._tag_deletions:
            updates[tag] = hszinc.REMOVE

        op = self._ENTITY_TAG_UPDATE_OPERATION(entity, updates)
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    def revert(self, tags=None):
        """
        Revert the named attribute changes, or all changes.
        """
        if tags is None:
            self._tag_updates = {}
            self._tag_deletions = set()
        else:
            for tag in tags:
                self._tag_updates.pop(tag, None)
                self._tag_deletions.discard(tag)

    def __iter__(self):
        """
        Iterate over the tags present.
        """
        return iter(self._tag_names)

    def __len__(self):
        """
        Return the number of tags present.
        """
        return len(self._tag_names)

    def __getitem__(self, tag):
        """
        Return the value of a tag.
        """
        if tag in self._tag_deletions:
            raise KeyError(tag)

        try:
            return self._tag_updates[tag]
        except KeyError:
            return self._tags[tag]

    def __setitem__(self, tag, value):
        """
        Set the value of a tag.
        """
        if value is hszinc.REMOVE:
            del self[tag]
            return

        self._tag_updates[tag] = value
        self._tag_deletions.discard(tag)

    def __delitem__(self, tag):
        """
        Remove a tag.
        """
        self._tag_deletions.add(tag)
        self._tag_updates.pop(tag, None)

    @property
    def _tag_names(self):
        """
        Return a set of tag names present.
        """
        return (
            set(self._tags.keys()) | set(self._tag_updates.keys())
        ) - self._tag_deletions


class ReadOnlyEntityTags(BaseEntityTags, col.Mapping):
    pass


class MutableEntityTags(BaseMutableEntityTags, col.MutableMapping):
    pass
