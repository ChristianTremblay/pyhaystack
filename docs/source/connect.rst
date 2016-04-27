Connecting to a haystack server
===============================

Using Niagara AX
----------------

Example ::

    from pyhaystack.client.niagara import NiagaraHaystackSession
    import logging
    logging.root.setLevel(logging.DEBUG)
    session = NiagaraHaystackSession(uri='http://ip:port', username='user', password='myPassword')
    #session.read(filter_expr='site').result
    about = session.about()

