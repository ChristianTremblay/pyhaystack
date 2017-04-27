===============================
Connecting to a haystack server
===============================

Pyhaystack has support modules for various Project Haystack implementations,
as well as an extensible framework for adding support for more
implementations.

The core object in Pyhaystack is the
:py:class:`pyhaystack.client.session.HaystackSession` object, which manages
the user credentials, implements caching and provides the interface through
which you or your scripts interact.  This is an abstract class, for which
several sub-classes exist.

There are two ways to create a session instance:

* Directly: by importing the relevant class and calling its constructor.
* Via the `pyhaystack.connect` (also known as
  :py:func:`pyhaystack.client.get_instance`) factory.

The former works well for ad-hoc usage in terminal sessions such as Jupyter
Notebook, ipython and the plain Python shell.  The latter is recommended for
scripts that instantiate a session from a configuration file.

Usage hints
-----------

Logging messages in Jupyter Notebook
""""""""""""""""""""""""""""""""""""

For interactive users using the Jupyter Notebook, the Jupyter notebook
configures its logs to only show messages with severity "warning" or higher.
To display logging messages at a lower level, run the following in your
session:

::

        import logging
        logging.getLogger().setLevel(logging.INFO)      # or DEBUG

Then log messages will appear in your session.

On-Demand connection
""""""""""""""""""""

Pyhaystack uses a feature called "lazy evaluation" to handle the actual log-in
session, and so will remain dormant after the session instance is connected
until a request is made.

If, when making a request, pyhaystack detects that it has been disconnected,
it will attempt to re-connect automatically.

Loading from a file
"""""""""""""""""""

The `connect` approach lends itself well to storing the connection
details in a plaintext file using either JSON or YAML format.  e.g. given the
file `my-haystack-server.json`:

::

    {
        "implementation": "skyspark",
        "uri": "http://ip:port",
        "username": "user",
        "password": "password",
        "project": "my_project",
        "pint": true
    }

This can be instantiated like this:

::

    import json
    import pyhaystack
    session = pyhaystack.connect(
        **json.load(
            open("my-haystack-server.json","r")
        )
    )

(Similarly for YAML, `import yaml` and use `yaml.safe_load`.)

Base session options
--------------------

:py:class:`pyhaystack.client.session.HaystackSession` has the following base
arguments.  All subclasses should pass these values though as keyword
arguments, so all should be usable.

* `uri`: This is the base URI used to access the Project Haystack server.

* `grid_format`: This selects the grid serialisation format for the Project
  Haystack server.  Some (e.g. nHaystack/Niagara AX) only support ZINC
  serialisation, where as others (such as WideSky) work better with JSON.
  Most of the time, the default here will be selected appropriate for the
  underlying server implementation.  Valid values are `zinc` and `json`.

* `http_client`: This selects which HTTP client implementation to use for the
  session instance.  pyhaystack at the moment just has two implementations:

  * :py:class:`pyhaystack.client.http.sync.SyncHttpClient`:
    a synchronous HTTP client based on the Python Requests library.  (default)

  * :py:class:`pyhaystack.client.http.dummy.DummyHttpClient`:
    an asynchronous dummy HTTP client used for writing unit tests.

  There are plans to implement asynchronous HTTP clients for various Python
  asynchronous frameworks (e.g. asyncio, TornadoWeb, Twisted, etc) in the
  future.

* `http_args`: This is a `dict` of keyword arguments that are passed to the
  constructor of the `http_client` class used to create a HTTP client
  instance.  If `None` is given, then it is assumed that no arguments are
  required.

* `tagging_model`: This is used by the high-level entity interface to allow
  Python objects to be created using various mix-ins based on the tags
  attached to the entity.  The default model,
  :py:class:`pyhaystack.client.entity.models.haystack.HaystackTaggingModel`
  assumes a standard Project Haystack tagging model and should suit most
  users.

* `pint`: This boolean passed to the :py:mod:`hszinc` module to enable use of
  the :py:mod:`pint` quantity classes (providing on-the-fly unit conversion).
  By default, this is `False`.

* `log`: An instance of :py:class:`logging.Logger` used for session logging
  messages.  If not given, then a logger named
  `pyhaystack.client.${CLASS_NAME}` is created.

* `cache_expiry`: An integer or floating-point value representing the period
  of time before `about`/`formats`/`ops` response cache expires.  The default
  is one hour.

HTTP client options (`http_client` and `http_args`)
"""""""""""""""""""""""""""""""""""""""""""""""""""

The HTTP client interface is written with asynchronous HTTP clients in mind
using a callback-style interface.  Internally, the `HaystackSession` class does
this:

::

        if http_args is None:
            http_args = {}

        # … etc …

        # Create the HTTP client object
        if bool(http_args.pop('debug',None)) and ('log' not in http_args):
            http_args['log'] = log.getChild('http_client')
        self._client = http_client(uri=uri, **http_args)

With the exception of the `debug` and `log` parameters, everything else is
passed through verbatim to the underlying HTTP client class.  The following
are the most useful arguments for `http_args`:

* `log`: If given, this is an instance of a :py:class:`logging.Logger` class
  that will be used for log messages from the HTTP client itself.

* `debug`: A boolean flag that enables HTTP client debugging.  If given, the
  `HaystackSession` will create a new :py:class:`logging.Logger` class for the
  HTTP client (actually, a child logger of its own logger) for HTTP client
  debug messages.

* `timeout`: an integer or floating-point value that specifies the HTTP
  request time-out delay in seconds.

* `proxies`: A `dict` that maps the host name and protocol of a target server
  to the URI for a local HTTP proxy server to use for that server.

* `tls_verify`: TLS verification of server certificates.  IF set to `True`,
  then the server's HTTP certificate will be verified against CA certificates
  known to the Python process.  If you use a custom CA, then this should be
  set to the full filesystem path to where that CA certificate is stored.
  Verification can be skipped by setting this to `False` (*not* recommended).

  When using a custom CA, the full certificate chain is required.  This is
  usually done by converting all relevant intermediate certificates to PEM
  format (aka `.crt` files) and concatenated in order, that is:

  1. the certificate for the CA that signed your server's certificate
  2. the certificate for the CA that signed *that* CA's certificate
  3. … etc
  4. the certificate for the root CA.

  If the root CA signed the server's certificate, then the chain is literally
  the root CA's certificate itself.  Note that your server's certificate is
  *NOT* part of the bundle.

* `tls_cert`: TLS client certificate.  This is used to authenticate the
  Pyhaystack client to a Project Haystack server using TLS client authentication.
  It should either be the full path to a combined certificate/key in PEM
  format, or a `tuple` of the form `(tls_client_cert, tls_client_key)` where
  both `tls_client_cert` and `tls_client_key` are full paths to the relevant
  files.

The base class also supports some additional parameters that may be helpful in
very specialised environments.

* `params`: a `dict` of URI query parameters to add to *all* requests.

* `headers`: a `dict` of HTTP headers to add to *all* requests.

* `cookies`: a `dict` of HTTP cookies to add to *all* requests.

* `auth`: Authentication credentials, in the form of a
  :py:class:`pyhaystack.client.http.auth.AuthenticationCredentials`
  sub-class.

Connecting to specific Haystack server implementations
------------------------------------------------------

Niagara AX (nHaystack)
""""""""""""""""""""""

Specific arguments
^^^^^^^^^^^^^^^^^^

In addition to those supported by the base class, the following constructor
arguments are supported:

* `username`: The username to use when authenticating with nHaystack
* `password`: The password to use when authenticating with nHaystack

Direct approach
^^^^^^^^^^^^^^^

::

    from pyhaystack.client.niagara import NiagaraHaystackSession
    session = NiagaraHaystackSession(uri='http://ip:port',
                                    username='user',
                                    password='myPassword',
                                    pint=True)

`connect()` approach
^^^^^^^^^^^^^^^^^^^^^^^^^

::

    import pyhaystack
    session = pyhaystack.connect(implementation='ax',
                            uri='http://ip:port',
                            username='user',
                            password='myPassword',
                            pint=True)

VRT Widesky
"""""""""""

Specific arguments
^^^^^^^^^^^^^^^^^^

In addition to those supported by the base class, the following constructor
arguments are supported:

* `username`: The email address to use when authenticating with WideSky
* `password`: The password to use when authenticating with WideSky
* `client_id`: The OAuth2 client identity to use when authenticating with
  WideSky.
* `client_secret`: The OAuth2 client secret to use when authenticating with
  WideSky.

Direct approach
^^^^^^^^^^^^^^^

::

    from pyhaystack.client.widesky import WideskyHaystackSession
    session = WideskyHaystackSession(
                    uri='https://yourtenant.on.widesky.cloud/reference',
                    username='user', password='my_password',
                    client_id='my_id', client_secret='my_secret'
                    pint=True)

`connect()` approach
^^^^^^^^^^^^^^^^^^^^^^^^^

::

    import pyhaystack
    session = pyhaystack.connect(implementation='widesky',
            uri='https://yourtenant.on.widesky.cloud/reference',
            username='user', password='my_password',
            client_id='my_id', client_secret='my_secret'
            pint=True)

Skyspark
""""""""

Specific arguments
^^^^^^^^^^^^^^^^^^

In addition to those supported by the base class, the following constructor
arguments are supported:

* `username`: The username to use when authenticating with SkySpark
* `password`: The password to use when authenticating with SkySpark
* `project`: The name of the SkySpark project instance.

Direct approach
^^^^^^^^^^^^^^^

::

    from pyhaystack.client.skyspark import SkysparkHaystackSession
    session = SkysparkHaystackSession(uri='http://ip:port',
                                    username='user',
                                    password='my_password',
                                    project='my_project'
                                    pint=True)

`connect()` approach
^^^^^^^^^^^^^^^^^^^^^^^^^

::

    import pyhaystack
    session = pyhaystack.connect(implementation='skyspark',
                                    uri='http://ip:port',
                                    username='user',
                                    password='my_password',
                                    project='my_project'
                                    pint=True)

----------
Next steps
----------

Having created a session instance, you're ready to start issuing requests,
which is covered in the next section.
