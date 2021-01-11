#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VRT WideSky operation implementations.
"""

import hszinc
import fysom
import json
import base64
import semver

from ....util import state
from ....util.asyncexc import AsynchronousException
from ..grid import BaseAuthOperation
from ..entity import EntityRetrieveOperation
from ..feature import HasFeaturesOperation
from ...session import HaystackSession


class WideskyAuthenticateOperation(state.HaystackOperation):
    """
    An implementation of the log-in procedure for WideSky.  WideSky uses
    a M2M variant of OAuth2.0 to authenticate users.
    """

    def __init__(self, session, retries=0):
        """
        Attempt to log in to the VRT WideSky server.  The procedure is as
        follows:

            POST to auth_dir URI:
                Headers:
                    Accept: application/json
                    Authorization: Basic [BASE64:"[ID]:[SECRET]"]
                    Content-Type: application/json
                Body: {
                    username: "[USER]", password: "[PASSWORD]",
                    grant_type: "password"
                }
            EXPECT reply:
                Headers:
                    Content-Type: application/json
                Body:
                    {
                        access_token: ..., refresh_token: ...,
                        expires_in: ..., token_type: ...
                    }

        :param session: Haystack HTTP session object.
        :param retries: Number of retries permitted in case of failure.
        """

        super(WideskyAuthenticateOperation, self).__init__()
        self._auth_headers = {
            "Authorization": (
                u"Basic %s"
                % base64.b64encode(
                    ":".join([session._client_id, session._client_secret]).encode(
                        "utf-8"
                    )
                ).decode("us-ascii")
            ).encode("us-ascii"),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self._auth_body = json.dumps(
            {
                "username": session._username,
                "password": session._password,
                "grant_type": "password",
            }
        ).encode("utf-8")
        self._session = session
        self._retries = retries
        self._auth_result = None

        self._state_machine = fysom.Fysom(
            initial="init",
            final="done",
            events=[
                # Event             Current State       New State
                ("do_login", ["init", "failed"], "login"),
                ("login_done", "login", "done"),
                ("exception", "*", "failed"),
                ("retry", "failed", "login"),
                ("abort", "failed", "done"),
            ],
            callbacks={
                "onenterlogin": self._do_login,
                "onenterfailed": self._do_fail_retry,
                "onenterdone": self._do_done,
            },
        )

    def go(self):
        """
        Start the request.
        """
        # Are we logged in?
        try:
            self._state_machine.do_login()
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _do_login(self, event):
        try:
            self._session._post(
                self._session._auth_dir,
                self._on_login,
                body=self._auth_body,
                headers=self._auth_headers,
                exclude_headers=True,
                api=False,
            )
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _on_login(self, response):
        """
        See if the login succeeded.
        """
        try:
            if isinstance(response, AsynchronousException):
                response.reraise()

            content_type = response.content_type
            if content_type is None:
                raise ValueError("No content-type given in reply")
            if content_type != "application/json":
                raise ValueError("Invalid content type received: %s" % content_type)

            # Decode JSON reply
            reply = json.loads(response.text)
            for key in ("token_type", "access_token", "expires_in"):
                if key not in reply:
                    raise ValueError("Missing %s in reply :%s" % (key, reply))

            self._state_machine.login_done(result=reply)
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _do_fail_retry(self, event):
        """
        Determine whether we retry or fail outright.
        """
        if self._retries > 0:
            self._retries -= 1
            self._state_machine.retry()
        else:
            self._state_machine.abort(result=event.result)

    def _do_done(self, event):
        """
        Return the result from the state machine.
        """
        self._done(event.result)


class CreateEntityOperation(EntityRetrieveOperation):
    """
    Operation for creating entity instances.
    """

    def __init__(self, session, entities, single):
        """
        :param session: Haystack HTTP session object.
        :param entities: A list of entities to create.
        """
        self._log = session._log.getChild("create_entity")
        super(CreateEntityOperation, self).__init__(session, single)
        self._new_entities = entities
        self._state_machine = fysom.Fysom(
            initial="init",
            final="done",
            events=[
                # Event             Current State       New State
                ("send_create", "init", "create"),
                ("read_done", "create", "done"),
                ("exception", "*", "done"),
            ],
            callbacks={"onenterdone": self._do_done},
        )

    def go(self):
        """
        Start the request, preprocess and submit create request.
        """
        self._state_machine.send_create()
        # Ensure IDs are basenames.
        def _preprocess_entity(e):
            if not isinstance(e, dict):
                raise TypeError("%r is not a dict" % e)
            e = e.copy()
            if "id" in e:
                e_id = e.pop("id")
                if isinstance(e_id, hszinc.Ref):
                    e_id = e_id.name
                if "." in e_id:
                    e_id = e_id.split(".")[-1]
                e["id"] = hszinc.Ref(e_id)
            return e

        entities = list(map(_preprocess_entity, self._new_entities))
        self._session.create(entities, callback=self._on_read)


class WideSkyHasFeaturesOperation(HasFeaturesOperation):
    def __init__(self, session, features, **kwargs):
        super(WideSkyHasFeaturesOperation, self).__init__(session, features, **kwargs)

        # Turn on retrieval of 'about' version data.
        self._need_about = True

    def _check_features(self):
        res = super(WideSkyHasFeaturesOperation, self)._check_features()

        # Ensure this is WideSky
        if self._about_data["productName"] not in (
            "Widesky Semantic Database Toolkit",
            "WideSky",
        ):
            # Not recognised, stop here.
            return res

        # Get the WideSky version, preferring moduleVersion over productVersion
        ver = self._about_data.get("moduleVersion", self._about_data["productVersion"])
        for feature in self._features:
            if feature in (
                HaystackSession.FEATURE_HISREAD_MULTI,
                HaystackSession.FEATURE_HISWRITE_MULTI,
            ):
                try:
                    res[feature] = semver.match(ver, ">=0.5.0")
                except ValueError:
                    # Unrecognised version string
                    return res
            elif feature == HaystackSession.FEATURE_ID_UUID:
                try:
                    res[feature] = semver.match(ver, ">=0.8.0")
                except ValueError:
                    return res
        return res


class WideSkyPasswordChangeOperation(BaseAuthOperation):
    """
    The Password Change operation implements the logic required to change a
    user's password.
    """

    def __init__(self, session, new_password, **kwargs):
        super(WideSkyPasswordChangeOperation, self).__init__(
            session=session, uri="user/updatePassword", **kwargs
        )
        self._new_password = new_password
        self._state_machine = fysom.Fysom(
            initial="init",
            final="done",
            events=[
                # Event  Current State  New State
                ("send_update", "init", "update"),
                ("update_done", "update", "done"),
                ("exception", "*", "done"),
            ],
            callbacks={"onsend_update": self._do_submit, "onenterdone": self._do_done},
        )

    def go(self):
        """
        Start the request.
        """
        try:
            self._state_machine.send_update()
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _do_submit(self, event):
        """
        Change the current logged in user's password.
        """
        try:
            self._session._post(
                uri=self._uri,
                callback=self._update_done,
                body=json.dumps({"newPassword": self._new_password}),
                headers={"Content-Type": "application/json"},
                api=False,
            )
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _update_done(self, response):
        try:
            if isinstance(response, AsynchronousException):
                response.reraise()

            self._state_machine.update_done(result=None)
        except:  # Catch all exceptions to pass to caller.
            self._state_machine.exception(result=AsynchronousException())

    def _do_done(self, event):
        """
        Return the result from the state machine.
        """
        self._done(event.result)
