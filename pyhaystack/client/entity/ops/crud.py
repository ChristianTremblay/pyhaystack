#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Entity CRUD state machines.
These are state machines that perform CRUD operations on entities at a
high-level.
"""

import hszinc
import fysom

from ....util.state import HaystackOperation
from ....util.asyncexc import AsynchronousException


class EntityTagUpdateOperation(HaystackOperation):
    """
    Tag update state machine.  This returns the entity instance that was
    updated on success.
    """

    def __init__(self, entity, updates):
        """
        Initialise a request for the named IDs.

        :param session: Haystack HTTP session object.
        """
        super(EntityTagUpdateOperation, self).__init__(result_copy=False)
        self._log = entity._session._log.getChild("update_tags")
        self._entity = entity
        self._updates = updates

        self._state_machine = fysom.Fysom(
            initial="init",
            final="done",
            events=[
                # Event             Current State       New State
                ("do_update", "init", "update"),
                ("update_done", "update", "done"),
                ("exception", "*", "done"),
            ],
            callbacks={"onenterdone": self._do_done},
        )

    def go(self):
        """
        Start the request, check cache for existing entities.
        """
        self._state_machine.do_update()
        self._entity._session.update(self._updates, callback=self._on_update)

    def _on_update(self, operation, **kwargs):
        """
        Process the grid, updating the tags on our entity.
        """
        try:
            # See if the read succeeded.
            grid = operation.result

            # Iterate over each row:
            for row in grid:
                row = row.copy()
                entity_id = row.pop("id")
                if (entity_id is None) or (entity_id.name != self._entity.id.name):
                    # Not for us!
                    self._log.debug(
                        "Ignoring row (%s does not match %s) %r",
                        entity_id,
                        self._entity.id,
                        row,
                    )
                    continue

                self._entity.tags._update_tags(row)
                self._entity.tags.revert()
                self._log.debug("Processed row %r", row)
            self._state_machine.update_done(result=self._entity)
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _do_done(self, event):
        """
        Return the result from the state machine.
        """
        self._done(event.result)
