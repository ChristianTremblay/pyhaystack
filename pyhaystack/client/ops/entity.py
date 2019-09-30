#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Entity state machines.  These are state machines that perform CRUD operations
on entities.
"""

import hszinc
import fysom

from ...util import state
from ...util.asyncexc import AsynchronousException
from ...exception import HaystackError


class EntityRetrieveOperation(state.HaystackOperation):
    """
    Base class for retrieving entity instances.
    """

    def __init__(self, session, single):
        """
        Initialise a request for the named IDs.

        :param session: Haystack HTTP session object.
        """
        single = bool(single)

        super(EntityRetrieveOperation, self).__init__(
            result_deepcopy=False, result_copy=not single
        )
        self._session = session
        self._entities = {}
        self._single = single

    def _on_read(self, operation, **kwargs):
        """
        Process the grid, updating existing items.
        """
        try:
            # See if the read succeeded.
            try:
                grid = operation.result
            except HaystackError as e:
                # Is this a "not found" error?
                if str(e).startswith("HNotFoundError"):
                    raise NameError("No matching entity found")
                raise

            self._log.debug("Received grid: %s", grid)

            # Iterate over each row:
            for row in grid:
                # Ignore rows that don't specify an ID.
                if "id" not in row:
                    continue

                row = row.copy()
                entity_ref = row.pop("id")

                # This entity does not exist
                if entity_ref is None:
                    continue

                entity_id = entity_ref.name

                try:
                    entity = self._entities[entity_id]
                    entity._update_tags(row)
                except KeyError:
                    try:
                        entity = self._session._entities[entity_id]
                        entity._update_tags(row)
                    except KeyError:
                        entity = self._session._tagging_model.create_entity(
                            entity_id, row
                        )

                # Stash/update entity references.
                self._session._entities[entity_id] = entity
                self._entities[entity_id] = entity

            if self._single:
                try:
                    result = list(self._entities.values())[0]
                except IndexError:
                    raise NameError("No matching entity found")
            else:
                result = self._entities
            self._state_machine.read_done(result=result)
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _do_done(self, event):
        """
        Return the result from the state machine.
        """
        self._done(event.result)


class GetEntityOperation(EntityRetrieveOperation):
    """
    Operation for retrieving entity instances by ID.  This operation peforms
    the following steps::

        If refresh_all is False:
        # State: init
            For each entity_id in entity_ids:
                If entity_id exists in cache:
                    Retrieve and store entity from cache.
                    Add entity_id to list got_ids.
            For each entity_id in got_ids:
                Discard entity_id from entity_ids.
        If entity_ids is not empty:
        # State: read
            Perform a low-level read of the IDs.
            For each row returned in grid:
                If entity is not in cache:
                    Create new Entity instances for each row returned.
                Else:
                    Update existing Entity instance with new row data.
            Add the new entity instances to cache and store.
        Return the stored entities.
        # State: done

    """

    def __init__(self, session, entity_ids, refresh_all, single):
        """
        Initialise a request for the named IDs.

        :param session: Haystack HTTP session object.
        :param entity_ids: A list of IDs to request.
        :param refresh_all: Refresh all entities, ignore existing content.
        """

        self._log = session._log.getChild("get_entity")
        super(GetEntityOperation, self).__init__(session, single)
        self._entity_ids = set(
            map(lambda r: r.name if isinstance(r, hszinc.Ref) else r, entity_ids)
        )
        self._todo = self._entity_ids.copy()
        self._refresh_all = refresh_all

        self._state_machine = fysom.Fysom(
            initial="init",
            final="done",
            events=[
                # Event             Current State       New State
                ("cache_checked", "init", "read"),
                ("read_done", "read", "done"),
                ("exception", "*", "done"),
            ],
            callbacks={"onenterread": self._do_read, "onenterdone": self._do_done},
        )

    def go(self):
        """
        Start the request, check cache for existing entities.
        """
        # See what is in cache.
        for entity_id in self._entity_ids:
            if isinstance(entity_id, hszinc.Ref):
                entity_id = entity_id.name

            try:
                self._entities[entity_id] = self._session._entities[entity_id]
            except KeyError:
                pass

        if not self._refresh_all:
            # Throw out what we've done
            list(map(self._todo.discard, list(self._entities.keys())))
        self._state_machine.cache_checked()

    def _do_read(self, event):
        """
        Read the entities that are left behind.
        """
        try:
            if bool(self._todo):
                self._session.read(ids=list(self._todo), callback=self._on_read)
            else:
                # Nothing needed to read.
                if self._single:
                    try:
                        result = list(self._entities.values())[0]
                    except IndexError:
                        raise NameError("No matching entity found")
                else:
                    result = self._entities
                self._state_machine.read_done(result=result)
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())


class FindEntityOperation(EntityRetrieveOperation):
    """
    Operation for retrieving entity instances by filter.
    This operation peforms the following steps::

        Issue a read instruction with the given filter:
            For each row returned in grid:
                If entity is not in cache:
                    Create new Entity instances for each row returned.
                Else:
                    Update existing Entity instance with new row data.
                Add the new entity instances to cache and store.
            Return the stored entities.
            # State: done

    """

    def __init__(self, session, filter_expr, limit, single):
        """
        Initialise a request for the named IDs.

        :param session: Haystack HTTP session object.
        :param filter_expr: Filter expression.
        :param limit: Maximum number of entities to fetch.
        """

        self._log = session._log.getChild("find_entity")
        super(FindEntityOperation, self).__init__(session, single)
        self._filter_expr = filter_expr
        self._limit = limit

        self._state_machine = fysom.Fysom(
            initial="init",
            final="done",
            events=[
                # Event             Current State       New State
                ("go", "init", "read"),
                ("read_done", "read", "done"),
                ("exception", "*", "done"),
            ],
            callbacks={"onenterdone": self._do_done},
        )

    def go(self):
        """
        Start the request, check cache for existing entities.
        """
        self._state_machine.go()
        self._session.read(
            filter_expr=self._filter_expr, limit=self._limit, callback=self._on_read
        )
