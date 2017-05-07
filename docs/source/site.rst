Operation basics
================

Pyhaystack's API is written around the concept of finite state machines.
At the base level, a simple state machine is used to retrieve the response
from one of the Project Haystack server operations.

When one of the low-level functions is called, it takes the arguments, does a
little processing then returns a state machine object.  Depending on the
implementation of the HTTP client being used, it either executes
*synchronously*, and will be returned to you in a "finalised" state, or it may
execute *asynchronously* in the background.

Operation state machine interface
---------------------------------

The base class for all operations is the
:py:class:`pyhaystack.util.state.HaystackOperation`.  The following methods
and properties are significant for client use:

* :py:attr:`pyhaystack.util.state.HaystackOperation.result`: The result of the
  state machine.  If the result was an exception, the exception will be
  re-raised.

* :py:attr:`pyhaystack.util.state.HaystackOperation.is_done`: Returns `True`
  if the operation is complete, `False` otherwise.

* :py:attr:`pyhaystack.util.state.HaystackOperation.is_failed`: Returns `True`
  if the operation failed, `False` otherwise.

* :py:meth:`pyhaystack.util.state.HaystackOperation.wait`: This blocks the
  current thread until the operation completes (or if `timeout` is specified,
  until that number of seconds expires).

* :py:attr:`pyhaystack.util.state.HaystackOperation.done_sig`: This is a
  :py:class:`signalslot.Signal` class that is "emitted" when the operation
  completes.

Synchronous usage
"""""""""""""""""

If you are using an asynchronous HTTP client running in a separate thread, you
can optionally block your local thread either temporarily or indefinitely
using the `wait` method.

When using the synchronous HTTP client, the `wait` is a no-op, since the state
machine is returned to the caller in a resolved state.  Thus, in synchronous
code, it is recommended to do the following:

::

        op = session.someoperation(arg1, arg2, arg3)
        op.wait()

        res = op.result
        # do something with res

This ensures that the operation is complete prior to retrieving its result.

Operation states
""""""""""""""""

The individual states of an operation depends on the type of state machine
being inspected, however all have a final state that can be checked by
inspecting the `is_done` property.  An operation is "done" if:

* the operation succeeded, in which case see the `result` property to retrieve
  the return value.

* the operation failed, in which case reading `result` will re-raise the
  exception.

Signals
"""""""

Pyhaystack uses the :py:module:`signalslot` module to provide a signal-based
interface using the observer pattern.  If you've ever worked with Qt, you'll
be familiar with how this works.

::

    def _on_op_done(operation, **kwargs):
        assert op.is_done # <- should not fire
        # Operation is done, do something with result.

    op = session.someoperation(arg1, arg2, arg3)
    op.done_sig.connect(_on_op_done)


The signal object has a single method, :py:meth:`signalslot.Signal.connect`,
which takes a method or function as an argument.  The passed-in method or
function needs to accept keyword arguments, and will receive a single
argument, `operation`, which will point to the instance of the
`HaystackOperation` that emitted it.

Asynchronous Exceptions
"""""""""""""""""""""""

When using signals, the behaviour is undefined if your "slot" throws an
exception, thus you should catch exceptions in your slots and handle those
elsewhere.  One helper class you can use for doing this is
:py:class:`pyhaystack.util.asyncexc.AsynchronousException`:

::

    from pyhaystack.asyncexc import AsynchronousException

    def async_func(callback):
        try:
            res = do_something()
        except:
            # Whoopsie!
            res = AsynchronousException()

        callback(res)


In the callback function, you can do something like this:

::

    def callback_from_async_func(result):
        try:
            if isinstance(result, AsynchronousException):
                result.reraise()
        except:
            # Handle your exception

If `result` is an exception, it'll be re-raised, allowing you to handle it in
your code.

Your first request
==================

You defined a session, now you want to connect to the server. The first
request you could make is called "about".

  About

    The about op queries basic information about the server.

    Request: empty grid

    Response: single row grid with following columns:

    * haystackVersion: Str version of REST implementation, must be "2.0"
    * tz: Str of server's default timezone
    * serverName: Str name of the server or project database
    * serverTime: current DateTime of server's clock
    * serverBootTime: DateTime when server was booted up
    * productName: Str name of the server software product
    * productUri: Uri of the product's web site
    * productVersion: Str version of the server software product
    * moduleName: module which implements Haystack server protocol if its a plug-in to the product
    * moduleVersion: Str version of moduleName

    -- http://project-haystack.org/doc/Ops

Using a synchronous request, you would use ::

   op = session.about()
   op.wait()

The output of `op.result` would print ::

    <Grid>
                Columns:
                        productName
                        moduleName
                        productVersion
                        serverTime
                        tz
                        moduleUri
                        serverName
                        productUri
                        serverBootTime
                        haystackVersion
                        moduleVersion
                Row    0: productName='Niagara AX', moduleName='nhaystack', productVersion='3.8.41.2', serverTime=datetime.datetime(2016, 4, 28, 21, 31, 33, 882000, tzinfo=<DstTzInfo 'America/Montreal' EDT-1 day, 20:00:00 DST>), tz='Montreal', moduleUri=Uri('https://bitbucket.org/jasondbriggs/nhaystack'), serverName='Servisys', productUri=Uri('http://www.tridium.com/'), serverBootTime=datetime.datetime(2016, 4, 5, 15, 9, 8, 119000, tzinfo=<DstTzInfo 'America/Montreal' EDT-1 day, 20:00:00 DST>), haystackVersion='2.0', moduleVersion='1.2.5.18.1'
    </Grid>

The return response is a :py:class:`hszinc.Grid` instance.

Session.nav()
-------------

`Session.nav()` let you navigate the structure of the Project Haystack server
in a manner native to that implementation of Project Haystack.  The following
is an example of the responses typically seen out of nHaystack.

::

    op = session.nav()
    op.wait()
    nav = op.result
    print(nav)

    Out[9]:
        <Grid>
                Columns:
                        dis
                        navId
                Row    0: dis='ComponentSpace', navId='slot:/'
                Row    1: dis='HistorySpace', navId='his:/'
                Row    2: dis='Site', navId='sep:/'
        </Grid>

    op = session.nav(nav_id='his:/')
    op.wait()
    nav = op.result
    print(nav)

    Out[10]:
        <Grid>
                Columns:
                        dis
                        stationName
                        navId
                Row    0: dis='mySite', stationName='mySite', navId='his:/mySite'
        </Grid>
    </Grid>

Higher Level Interface
======================

The session instance also provides a higher-level interface that exposes the
entities within Project Haystack as Python objects.  The two functions that
retrieve these entities are:

* :py:meth:`pyhaystack.client.session.HaystackSession.get_entity` and
* :py:meth:`pyhaystack.client.session.HaystackSession.find_entity`

Both are wrappers around the `read` operation that retrieve
:py:class:`pyhaystack.client.entity.entity.Entity` instances for the entities
returned.

`get_entity` expects a list of one or more fully qualified identifiers, and
will perform a `read` query listing those identifiers as given.

`find_entity` expects a filter expression, and performs a `read` specifying
the given string as the `filter` argument.  (Note: `find_entity` takes an
argument named `filter_expr` to avoid a clash with the built-in function
:py:func:`filter`.)

In both cases, a :py:class:`dict` is returned, where the keys are the
identifiers of matching entities and the values are the `Entity` instances
themselves.  Depending on the tags present, and the `tagging_model` passed to
the session, these `Entity` instances may include other mix-in classes as
well.

Building a filter string
------------------------

As a convenience, it is possible to build up a filter string using Python
objects, then take a string representation of that composite object to
generate a filter string.

The classes are in :py:module:`pyhaystack.util.filterbuilder`.  An example:

::

    from pyhaystack.util import filterbuilder as fb # for brevity

    op = session.find_entity(fb.Field('site') & \
            ((fb.Field('tz') == fb.Scalar('Brisbane')) \
              | (fb.Field('tz') == fb.Scalar('Montreal'))))
    op.wait()
    sites_in_brisbane_and_montreal = op.result

would return all sites that are in the Brisbane or Montreal timezones.

This is helpful in scenarios where you have to construct a filter
programmatically and wish to avoid the possibility of unsanitised data
corrupting your filter string.

Querying Sites
--------------

The site_ is

    "A site entity models a single facility using the site tag.
    A good rule of thumb is to model any building with its own
    street address as its own site. For example a campus is better
    modeled with each building as a site, versus treating the entire
    campus as one site."

    -- project-haystack

To browse a site you could use ::

    op = session.find_entity(filter_expr='site')
    op.wait()
    site = op.result

and get a dict containing all the information provided ::

    {'S.site': <@S.site: {area=BasicQuantity(0.0, 'ft²'), axSlotPath='slot:/site', axType='nhaystack:HSite', dis='site', geoAddr='2017', geoCity='thisTown', geoCountry='myCountry', geoLat=0.0, geoLon=0.0, geoPostalCode='', geoState='myState', geoStreet='myStreet', navName='site', site, tz='New_York'}>}

Using the default tagging model, because the entity has a `site` tag and a
`tz` tag, the resulting `Entity` class returned here will be subclasses of
the following:

* :py:class:`pyhaystack.client.entity.entity.Entity` (base class)
* :py:class:`pyhaystack.client.entity.mixins.site.SiteMixin` (mixin class)
* :py:class:`pyhaystack.client.entity.mixins.site.TzMixin` (mixin class)

A session have typically one site attached to it, but there could be more. As
a shortcut, pyhaystack provides properties on session to get the site:

::

    # Target the first site (returns a SiteTzEntity)
    session.site

    # Get a dict with all sites
    session.sites

.. _site : http://project-haystack.org/doc/Structure#site
