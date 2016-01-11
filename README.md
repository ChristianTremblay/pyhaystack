Pyhaystack is a module that allow python programs to connect to a haystack server [project-haystack.org](http://www.project-haystack.org).

Actually, connection can be established with Niagara Platform running the nhaystack module.

It's a work in progress and actually, main goal is to connect to server and retrive histories to make numeric analysis. Eventually, other options will be implemented through the REST API.

For this to work with [Anaconda](http://continuum.io/downloads) IPython Notebook in Windows, be sure to use "python setup.py install" using the Anaconda Command Prompt in Windows.
If not, module will be installed for System path python but won't work in the environment of Anaconda IPython Notebook.

#Using pyhaystack
##Open a session with Haystack server

[![Join the chat at https://gitter.im/ChristianTremblay/pyhaystack](https://badges.gitter.im/ChristianTremblay/pyhaystack.svg)](https://gitter.im/ChristianTremblay/pyhaystack?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

```
#!python
    import pyhaystack.client.NiagaraAXClient as ax
    import pandas as pd
    import numpy as np
    %matplotlib inline
    import matplotlib.pyplot as plt
    import re
    import math
    session = ph.NiagaraAXConnection('http://serverIP/','user','password',[optional] zinc=True)

    """
    optional zinc parameter is a way to make it work with old Jace NPM2 devices. 
    Those devices aren't able to serve JSON messages due to a too old Java VM. 
    zinc=true will retrieve the zinc output of the server and re-create a Json message so pyhaystack will be able to work with a Json string.
    """"
```

![haystack1.JPG](https://bitbucket.org/repo/Anyjky/images/359755258-haystack1.JPG)


#Fetching data

I've been inspired by Skyspark way of reading haystack so I tried something here with the new function readAll wich is simply a way to pass a filter to a request and get the Json result back as a new class named haystackRead. haystackRead allows functions to facilitate the work ex :

* readDis returns a list of dis
* readId returns a list of id
* readCurVal returns a list of curVal
* showVal returns a dict with dis : curVal
* hasTrend returns True or False depending on the presence of the his tag on any Id
* hisRead returns a list of hisrecord 
         
```
#!python
    temp = session.readAll('(sensor and temp and air and (not discharge))').hisRead(start='2015-01-26',end='2015-01-30')

```


##Call list of histories

```
#!python
    hisList = session.hisAll()

```

##Get some trend records as list

```
#!python
    trends = session.hisRead(AND_search=['S-3','OA'], start='2014-10-10',end='2014-10-12')
    trends[0].data
    """"
    OR (with new readAll() function)
    """"
    temp = session.readAll('(sensor and temp and air and (not discharge))').hisRead(start='2015-01-26',end='2015-01-30')
```


![onerecord.jpg](https://bitbucket.org/repo/Anyjky/images/3727676776-onerecord.jpg)

# Use pandas to analyse data
##Compute mean by hour of this record
Using the "between_time" function you can also get this range of data for every day !


```
#!python
    hourlymean_day = trends[0].data.resample('h').between_time('08:00','17:00')
    hourlymean_day

```		

![hourlymean.jpg](https://bitbucket.org/repo/Anyjky/images/775575559-hourlymean.jpg)
##Plot a beautiful graph

	:::python
		hourlymean_day.plot(kind='bar')

![hourlymean_plotbar.jpg](https://bitbucket.org/repo/Anyjky/images/2795760219-hourlymean_plotbar.jpg)   
##Get some simple stats info on records
	
	:::python
		trends[0].simpleStats()

![simplestats.jpg](https://bitbucket.org/repo/Anyjky/images/1419979617-simplestats.jpg)
##Draw a distribution plots
Distribution plot draw a graph showing how many records are between 20-20.5degC, between 20,5-21degC, etc... 

	:::python
		trends[0].breakdownPlot()

![breakdownplot.jpg](https://bitbucket.org/repo/Anyjky/images/859471603-breakdownplot.jpg)