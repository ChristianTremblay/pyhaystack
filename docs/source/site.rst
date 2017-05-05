Your first request
===================
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

   about = session.about()

The output of "about" would print ::

    <GetGridOperation done: <Grid>
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
    </Grid>>

Session.nav()
-------------
Session.nav() let you see what's under the server. Result of the request coud look
like that ::

    session.nav().result

    Out[9]:
        <Grid>
        	Columns:
        		dis
        		navId
        	Row    0: dis='ComponentSpace', navId='slot:/'
        	Row    1: dis='HistorySpace', navId='his:/'
        	Row    2: dis='Site', navId='sep:/'
        </Grid>

    session.nav(nav_id='his:/').result

    Out[10]:
        <Grid>
        	Columns:
        		dis
        		stationName
        		navId
        	Row    0: dis='mySite', stationName='mySite', navId='his:/mySite'
        </Grid>

Site
----
The site_ is

    "A site entity models a single facility using the site tag.
    A good rule of thumb is to model any building with its own
    street address as its own site. For example a campus is better
    modeled with each building as a site, versus treating the entire
    campus as one site."

    -- project-haystack

To browse a site you will use ::

    site = session.find_entity(filter_expr='site').result

and get a dict containing all the information provided ::

    {'S.site': <@S.site: {area=BasicQuantity(0.0, 'ft²'), axSlotPath='slot:/site', axType='nhaystack:HSite', dis='site', geoAddr='2017', geoCity='thisTown', geoCountry='myCountry', geoLat=0.0, geoLon=0.0, geoPostalCode='', geoState='myState', geoStreet='myStreet', navName='site', site, tz='New_York'}>}


A session have typically one site attached to it, but there could be more. As a shortcut,
pyhaystack provide properties on session to get the site ::

    # Target the first site (returns a SiteTzEntity)
    session.site

    # Get a dict with all sites
    session.sites

.. _site : http://project-haystack.org/doc/Structure#site
