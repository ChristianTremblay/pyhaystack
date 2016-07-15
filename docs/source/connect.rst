Connecting to a haystack server
===============================

Using Niagara AX
----------------
::

    from pyhaystack.client.niagara import NiagaraHaystackSession
    session = NiagaraHaystackSession(uri='http://ip:port', 
                                    username='user', 
                                    password='myPassword',
                                    *pint=True)

Note that pint parameter is optionnal and default to False.

Using Widesky
--------------
::

    from pyhaystack.client.widesky import WideskyHaystackSession
    session = SkysparkHaystackSession(uri='http://ip:port', 
                                    username='user', 
                                    password='my_password', 
                                    client_id = 'my_id',
                                    client_secret = 'my_secret'
                                    *pint=True)
 

Using Skyspark
--------------
::
    
    from pyhaystack.client.skyspark import SkysparkHaystackSession
    session = SkysparkHaystackSession(uri='http://ip:port', 
                                    username='user', 
                                    password='my_password', 
                                    project = 'my_project'
                                    *pint=True)
 
On-Demand connection
---------------------
Once the session is initialized, it won't connect until it needs to.
Pyhaystack will benefit from the asynchronous framework and connect on demand.
The session will be connected and the request will be sent to the server.

If, when making a request, pyhaystack detects that it has been disconnected, 
it will re-connect automatically.

See next section to know more about requests.