#!python
# -*- coding: utf-8 -*-
"""
VRT Widesky low-level CRUD operation mix-in.  This is a mix-in for
HaystackSession that implements CRUD operations as used in VRT Widesky's
implementation of Project Haystack.

At present, this has not been adopted by other implementations.
"""

import hszinc
from six import string_types


class CRUDOpsMixin(object):
    """
    The CRUD operations mix-in implements low-level support for entity
    create / update / delete operation extensions to Project Haystack.
    (Read is not included, since that's part of the core standard.)
    """

    def create(self, entities, callback=None):
        """
        Create the entities listed.  If given a dict, we are creating a
        single entity, otherwise multiple entities may be given as individual
        dicts.

        Each dict must carry an `id` which is a string giving the unique
        fully qualified ID of the entity.  All other keys are taken to be
        tag values to attach to that entity, the values of which must be
        valid `hszinc` types.

        :param entities: The entities to be inserted.
        """
        return self._crud_op(
            "createRec", entities, callback, accept_status=(200, 400, 404)
        )

    def create_entity(self, entities, single=None, callback=None):
        """
        Create the entities listed, and return high-level entity instances for
        them.  This is a high-level convenience around the above `create`
        method.
        """
        if isinstance(entities, dict):
            entities = [entities]
            if single is None:
                single = True
        else:
            single = bool(single)

        op = self._CREATE_ENTITY_OPERATION(self, entities, single)
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    def update(self, entities, callback=None):
        """
        Update the entities listed.  If given a dict, we are creating a
        single entity, otherwise multiple entities may be given as individual
        dicts.

        Each dict must carry an `id` which is a string giving the unique
        fully qualified ID of the entity.  All other keys are taken to be
        tag values to update on that entity, the values of which must be
        valid `hszinc` types.

        :param entities: The entities to be updated.
        """
        return self._crud_op(
            "updateRec", entities, callback, accept_status=(200, 400, 404)
        )

    def delete(self, ids=None, filter_expr=None, callback=None):
        """
        Delete entities matching the given criteria.
        Either ids or filter_expr may be given.  ids may be given as a
        list or as a single ID string/reference.

        filter_expr is given as a string.  pyhaystack.util.filterbuilder
        may be useful for generating these programatically.

        :param ids: IDs of many entities to retrieve as a list
        :param filter_expr: A filter expression that describes the entities
                            of interest.
        """
        if isinstance(ids, string_types) or isinstance(ids, hszinc.Ref):
            # Make sure we always pass a list.
            ids = [ids]

        if bool(ids):
            if filter_expr is not None:
                raise ValueError("Either specify ids or filter_expr, not both")

            ids = [self._obj_to_ref(r) for r in ids]

            if len(ids) == 1:
                # Reading a single entity
                return self._get_grid("deleteRec", callback, args={"id": ids[0]})
            else:
                # Reading several entities
                grid = hszinc.Grid()
                grid.column["id"] = {}
                grid.extend([{"id": r} for r in ids])
                return self._post_grid("deleteRec", grid, callback)
        else:
            args = {"filter": filter_expr}
            return self._get_grid(
                "deleteRec", callback, args=args, accept_status=(200, 400, 404)
            )

    # Private methods

    def _crud_op(self, op, entities, callback, **kwargs):
        """
        Perform a repeated operation on the given entities with the given
        values for each entity.  `entities` should be a list of dicts, each
        dict having an `id` key that specifies the entity's ID and other keys
        giving the values.

        :param entities: The entities to be inserted.
        """
        if isinstance(entities, dict):
            # Convert single entity to list.
            entities = [entities]

        # Construct a list of columns
        all_columns = set()
        list(map(all_columns.update, [e.keys() for e in entities]))
        # We'll put 'id' first sort the others.
        if "id" in all_columns:
            all_columns.discard("id")
            all_columns = ["id"] + sorted(all_columns)
        else:
            all_columns = sorted(all_columns)

        # Construct the grid
        grid = hszinc.Grid()
        for column in all_columns:
            grid.column[column] = {}

        for entity in entities:
            # Take a copy
            entity = entity.copy()

            # Ensure 'id' is a ref
            if "id" in entity:
                entity["id"] = self._obj_to_ref(entity["id"])

            # Ensure all other columns are present
            for column in all_columns:
                if column not in entity:
                    entity[column] = None

            # Add to the grid
            grid.append(entity)

        # Post the grid
        return self._post_grid(op, grid, callback, **kwargs)
