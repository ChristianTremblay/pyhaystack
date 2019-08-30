#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Feature detection operation.  This is used to dynamically enable or disable
features of a client according to the server implementation.
"""

from ...util.asyncexc import AsynchronousException
from ...util import state
import fysom


class HasFeaturesOperation(state.HaystackOperation):
    """
    A base class to detect if a given set of features is present.
    """

    def __init__(self, session, features, cache=True):
        """
        Initialise a request for the grid with the given URI and arguments.

        :param session: Haystack HTTP session object.
        :param features: Iterable of features to check for.
        :param cache: Whether or not to use cache for this check.
        """
        super(HasFeaturesOperation, self).__init__()
        self._log = session._log.getChild("has_features")
        self._session = session
        self._features = set(features)
        self._cache = cache

        # Needed feature data.  If there are no extensions involved, just
        # compare the features to the op names to see if they're present.
        self._need_about = False
        self._need_formats = False
        self._need_ops = any([("/" not in feature) for feature in self._features])

        # Retrieved feature data
        self._about = None
        self._about_data = {}
        self._formats = None
        self._formats_data = {}
        self._ops = None
        self._ops_data = {}

        self._state_machine = fysom.Fysom(
            initial="init",
            final="done",
            events=[
                # Event             Current State       New State
                ("go", "init", "get_about"),
                ("about_done", "get_about", "get_formats"),
                ("formats_done", "get_formats", "get_ops"),
                ("ops_done", "get_ops", "check_features"),
                ("checked", "check_features", "done"),
                ("exception", "*", "done"),
            ],
            callbacks={
                "onenterget_about": self._do_get_about,
                "onenterget_formats": self._do_get_formats,
                "onenterget_ops": self._do_get_ops,
                "onentercheck_features": self._do_check_features,
                "onenterdone": self._do_done,
            },
        )

    def go(self):
        """
        Start the request.
        """
        self._log.debug(
            "Needed: about=%s, formats=%s, ops=%s",
            self._need_about,
            self._need_formats,
            self._need_ops,
        )
        self._state_machine.go()

    def _do_get_about(self, event):
        """
        Retrieve the 'about' grid, if needed.
        """
        try:
            if self._need_about:
                self._log.debug("Retrieving about data")
                self._session.about(callback=self._on_got_about, cache=self._cache)
            else:
                self._log.debug("Skipping about data")
                self._state_machine.about_done()
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _on_got_about(self, operation, **kwargs):
        """
        Store the result of the "about" request.
        """
        try:
            self._about = operation.result
            self._about_data = self._about[0]
            self._log.debug("Got about data: %s", self._about_data)
            self._state_machine.about_done()
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _do_get_formats(self, event):
        """
        Retrieve the 'formats' grid, if needed.
        """
        try:
            if self._need_formats:
                self._log.debug("Retrieving formats data")
                self._session.formats(callback=self._on_got_formats, cache=self._cache)
            else:
                self._log.debug("Skipping formats data")
                self._state_machine.formats_done()
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _on_got_formats(self, operation, **kwargs):
        """
        Store the result of the "formats" request.
        """
        try:
            self._formats = operation.result
            for row in self._formats:
                self._formats_data[row["mime"]] = row
            self._log.debug("Got formats data: ", self._formats_data)
            self._state_machine.formats_done()
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _do_get_ops(self, event):
        """
        Retrieve the 'ops' grid, if needed.
        """
        try:
            if self._need_ops:
                self._log.debug("Retrieving ops data")
                self._session.ops(callback=self._on_got_ops, cache=self._cache)
            else:
                self._log.debug("Skipping ops data")
                self._state_machine.ops_done()
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _on_got_ops(self, operation, **kwargs):
        """
        Store the result of the "ops" request.
        """
        try:
            self._ops = operation.result
            for row in self._ops:
                self._ops_data[row["name"]] = row
            self._log.debug("Got ops data: %s", self._ops_data)
            self._state_machine.ops_done()
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _do_check_features(self, event):
        """
        Check whether the features are present.
        """
        try:
            result = self._check_features()
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())
            return
        self._state_machine.checked(result=result)

    def _check_features(self):
        """
        Synchronous operation: check if the listed features are present.
        Subclasses should call update on the result of the parent.
        """
        res = {}
        for feature in self._features:
            if "/" in feature:
                # This is an extension
                res[feature] = False
            elif feature in self._ops_data:
                # This is a standard operation supported by the server
                res[feature] = True
            else:
                # Assume not supported
                res[feature] = False
        return res

    def _do_done(self, event):
        """
        Return the result from the state machine.
        """
        self._done(event.result)
