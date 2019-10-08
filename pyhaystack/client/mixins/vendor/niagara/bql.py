#!python
# -*- coding: utf-8 -*-
"""
Niagara allows BQL requests to browse the database

"""

from requests.compat import urljoin
import io
import pandas as pd

from ....ops.grid import BaseAuthOperation
from .....util.asyncexc import AsynchronousException

try:
    from urllib.parse import quote as quote_uri
except ImportError:
    # Python 2.7 dinosaur
    from urllib import quote as quote_uri


class BQLOperation(BaseAuthOperation):
    def __init__(self, session, bql, args=None, **kwargs):
        """
        Initialise a GET request for the BQL with the given request and arguments.

        :param session: Haystack HTTP session object.
        :param bql: BQL Request 
        :param args: Dictionary of key-value pairs to be given as arguments.
        """
        self._log = session._log.getChild("bql.%s" % bql)
        bql_request = "ord?" + quote_uri(bql) + "%7Cview:file:ITableToCsv"
        self.uri = urljoin(session._uri, bql_request)
        self._file_like_object = None
        super(BQLOperation, self).__init__(session=session, uri=self.uri, **kwargs)

    def _do_submit(self, event):
        """
        Submit the GET request to the haystack server.
        """

        try:
            self._session._get(
                self._uri, api=False, headers=self._headers, callback=self._on_response
            )
        except:  # Catch all exceptions to pass to caller.
            self._log.debug("Get fails", exc_info=1)
            self._state_machine.exception(result=AsynchronousException())

    def _on_response(self, response):
        """
        Process the response given back by the HTTP server.
        """
        try:
            # Does the session want to invoke any relevant hooks?
            # This allows a session to detect problems in the session and
            # abort the operation.
            if hasattr(self._session, "_on_http_grid_response"):
                self._session._on_http_grid_response(response)

            # Process the HTTP error, if any.
            if isinstance(response, AsynchronousException):
                response.reraise()

            # If we're expecting a raw response back, then just hand the
            # request object back and finish here.
            self._file_like_object = io.StringIO(response.body.decode("UTF-8"))
            df = pd.read_csv(self._file_like_object)
            self._state_machine.response_ok(result=df)
            return

        except:  # Catch all exceptions for the caller.
            self._log.debug("Parse fails", exc_info=1)
            self._state_machine.exception(result=AsynchronousException())


class BQLMixin(object):
    """
    This will add function needed to implement the BQL ops
    for Niagara clients

    """

    def _get_bql(self, bql, callback, cache=False, **kwargs):
        """
        Perform a HTTP GET of a BQL Request.
        """
        op = self._BQL_OPERATION(self, bql, cache=cache, **kwargs)
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op

    def get_bql(self, bql):
        """
        Helper to get a BQL sent to the Niagara device
        """
        return self._get_bql(bql, callback=lambda *a, **k: None)
