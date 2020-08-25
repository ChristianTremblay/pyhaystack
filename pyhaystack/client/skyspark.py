#!python
# -*- coding: utf-8 -*-
"""
Skyspark Client support
"""
import hszinc
from six import string_types

from .session import HaystackSession
from .ops.vendor.skyspark import SkysparkAuthenticateOperation
from .ops.vendor.skyspark_scram import SkysparkScramAuthenticateOperation
from .mixins.vendor.skyspark import evalexpr


class SkysparkHaystackSession(HaystackSession, evalexpr.EvalOpsMixin):
    """
    The SkysparkHaystackSession class implements some base support for
    Skyspark servers.
    """

    _AUTH_OPERATION = SkysparkAuthenticateOperation

    def __init__(self, uri, username, password, project="", **kwargs):
        """
        Initialise a Skyspark Project Haystack session handler.

        :param uri: Base URI for the Haystack installation.
        :param username: Authentication user name.
        :param password: Authentication password.
        :param project: Skyspark project name
        """
        super(SkysparkHaystackSession, self).__init__(uri, "api/%s" % project, **kwargs)
        self._project = project
        self._username = username
        self._password = password
        self._authenticated = False

    @property
    def is_logged_in(self):
        """
        Return true if the user is logged in.
        """
        return self._authenticated

    # Private methods/properties

    def _on_authenticate_done(self, operation, **kwargs):
        """
        Process the result of an authentication operation.  This needs to be
        implemented in the subclass and should, at minimum, set a flag in the
        subclass to indicate the authentication state and clear the _auth_op
        attribute on the base class.
        """
        try:
            cookies = operation.result
            self._authenticated = True
            self._client.cookies = cookies
        except:
            self._authenticated = False
            self._client.cookies = None
        finally:
            self._auth_op = None


class SkysparkScramHaystackSession(HaystackSession, evalexpr.EvalOpsMixin):
    """
    The SkysparkHaystackSession class implements some base support for
    Skyspark servers.
    """

    _AUTH_OPERATION = SkysparkScramAuthenticateOperation

    def __init__(self, uri, username, password, project, **kwargs):
        """
        Initialise a Skyspark Project Haystack session handler.

        :param uri: Base URI for the Haystack installation.
        :param username: Authentication user name.
        :param password: Authentication password.
        :param project: Skyspark project name
        """
        super(SkysparkScramHaystackSession, self).__init__(
            uri, "api/%s" % project, **kwargs
        )

        self._username = username
        self._password = password
        self._project = project
        self._authenticated = False
        self._authToken = None
        self._attestKey = None

    @property
    def is_logged_in(self):
        """
        Return true if the user is logged in.
        """
        return self._authenticated

    # Private methods/properties

    def _on_authenticate_done(self, operation, **kwargs):
        """
        Process the result of an authentication operation.  This needs to be
        implemented in the subclass and should, at minimum, set a flag in the
        subclass to indicate the authentication state and clear the _auth_op
        attribute on the base class.
        """
        try:

            op_result = operation.result
            header = op_result["header"]
            # self._key = op_result["key"]
            # self._authToken = header['Authorization'].split('=')[-1]
            # print(self._authToken)
            # print('KEY :', self._key)
            self._authenticated = True
            self._client.cookies = None
            self._client.headers = header
            print(self._client.headers)
        except:
            self._authenticated = False
            self._client.cookies = None
        finally:
            self._auth_op = None

    def logout(self):
        """close session when leaving context by trick given by Brian Frank

        https://www.skyfoundry.com/forum/topic/5282#c1

        but beware that this is not standard!"""

        # TODO: Rewrite this when a standard way to close sessions is
        #       implemented in Skyspark.
        def callback(response):
            try:
                status_code = response.status_code

            except AttributeError as error:
                status_code = -1

            if status_code != 200:
                self._log.warning("Failed to close skyspark session")
                self._log.warning("status_code={}".format(status_code))
            else:
                self._log.info("You've been properly disconnected")

        self._get("/user/logout", callback, api=False)

    def _on_his_read(self, point, rng, callback, **kwargs):
        """
        Skyspark will not accept GET request for his_read by default
        [ref : https://project-haystack.org/forum/topic/787#c6]
            The default behavior of SkySpark is now to disallow GET requests 
            non-idempotent operations. So its still allowed on certain operations 
            such as about, formats, read. However as Chris said it can be toggled 
            back on using Settings|API for backward compatibility.

            However as a recommendation I think we should always be using POST as 
            a safer alternative. Using GET for ops with side-effects is against 
            the HTTP spec. Plus it is an attack vector if cookies are involved. 
            And it provides a more precise way to pass the request payload.

            Its not really from a theoretical perspective. But in SkySpark 
            we allow customers to generate histories using their own custom 
            functions. So from a security perspective we took the safest route 
            and consider it to potentially have side effects.
            If your code is all using GET, then just have the customer set 
            Settings|API allowGetWithSideEffects flag to false and it should all work.
        """
        if isinstance(rng, slice):
            str_rng = ",".join([hszinc.dump_scalar(p) for p in (rng.start, rng.stop)])
        elif not isinstance(rng, string_types):
            str_rng = hszinc.dump_scalar(rng)
        else:
            # Better be valid!
            str_rng = rng

        col_list = [("id", []), ("range", [])]
        his_grid = hszinc.grid.Grid(columns=col_list)
        his_grid.insert(0, {"id": self._obj_to_ref(point), "range": str_rng})
        # his_grid = {"meta": {"ver":"2.0"},"cols":[{"name":"id"},{"name":"range"}],"rows":[{"id":"r:p:demo:r:255873a0-68a48b9f","range":"s:today"}]}
        headers = self._client.headers
        # headers[b"SkyArc-Attest-Key"] = self._key
        print(his_grid)
        return self._post_grid(
            "hisRead",
            his_grid,
            callback,
            headers=headers,
            exclude_cookies=True,
            **kwargs
        )
