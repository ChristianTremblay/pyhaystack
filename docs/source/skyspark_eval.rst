Eval
=========
Eval is used to evaluate any Axon expression.
Request: a grid with one column called expr and one row with Str expression to evaluate.
Response: result of the expression converted to a grid using Etc.toGrid
If an error occurs an error grid is returned.
        
        

Usage
++++++
    // GET request
    /api/demo/eval?expr=readAll(site)
    
    // POST request
    ver:"2.0"
    expr
    "readAll(site)"


::

        result = session.get_eval('readAll(site)').result


