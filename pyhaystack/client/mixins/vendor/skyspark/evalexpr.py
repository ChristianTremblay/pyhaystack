#!python
# -*- coding: utf-8 -*-
"""
Skyspark allows custom functions to be called by a eval op

This is a BETA function that will need to be tested by users

"""


class EvalOpsMixin(object):
    """
    This will add function needed to implement the eval ops
    for skyspark clients

    [ref : https://www.beyon-d.net/doc/docSkySpark/Ops.html]
    """

    def get_eval(self, arg_expr):
        """
        Eval
        ====
        Eval is used to evaluate any Axon expression.
        Request: a grid with one column called expr and one row with Str expression to evaluate.
        Response: result of the expression converted to a grid using Etc.toGrid
        If an error occurs an error grid is returned.
        Examples:
        
        // GET request
        /api/demo/eval?expr=readAll(site)
        
        // POST request
        ver:"2.0"
        expr
        "readAll(site)"
        """

        url = "eval?expr=%s" % arg_expr
        return self._get_grid(url, callback=lambda *a, **k: None)


#    ===========================
#    This function is commented and not working. I don't have anything to test
#    This should return multiple grids and I don't know how pyhaystack will react
#    ===========================

#    def get_evalall(self, arg_expr):
#        """
#        Eval All
#        ========
#        If you have multiple expressions to evaluate, you can POST a grid to the evalAll URI.
#        The posted grid specifies a row for each expression to evaluate with the expr column.
#        The results are returned as a encoded a list of grids based on content negioation in the same
#        order as the request expressions.
#
#        If an error occurs for any one expression, then an error grid is returned as the result
#        of that expression. All expressions are evaluated regardless of any partial failure.
#        If you wish to perform an atomic series of expressions, then you can evaluate one expression
#        inside a do block.
#
#        The evalAll operation is not a Haystack compliant operation. Its request is compliant,
#        but the response returns a list of multiple grids.
#
#        Reusing Intermediate Results
#        ----------------------------
#
#        The evalAll API supports the ability to reuse intermediate expressions to feed
#        additional expressions. For example lets say we want to return a history query
#        and a daily rollup of both min and max. The expensive way would be to re-evaluate
#        the history query three times:
#
#        ver:"2.0"
#        expr
#        "readAll(kw).hisRead(thisWeek)"
#        "readAll(kw).hisRead(thisWeek).hisRollup(max,1day)"
#        "readAll(kw).hisRead(thisWeek).hisRollup(min,1day)"
#
#        Instead we can add an args column to reuse previous expressions as arguments.
#        In this case we can evaluate the history query once, then reuse it for the two rollups:
#
#        ver:"2.0"
#        expr,args
#        "readAll(kw).hisRead(thisWeek)",
#        "hisRollup(_,max,1day)","0"
#        "hisRollup(_,min,1day)","0"
#
#        The args column is formatted as a list of strings separated by comma. The arguments
#        must be an integer index into the row to use as argument. Or the value "prev" may be
#        used to indicate the previous row. In order to use the args feature, the expression must
#        evaluate to a function with the required number of parameters. This is typically
#        accomplished via partial application.
#        """
#
#        url = '/evalAll?expr=%s' % arg_expr
#        result = self.session._post_grid(url, callback=lambda *a, **k: None)
