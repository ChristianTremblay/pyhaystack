Pyhaystack is a module that allow python programs to connect to a haystack server [project-haystack.org](http://www.project-haystack.org).

Actually, connection can be established with Niagara Platform running the nhaystack module.

For this to work with Anaconda IPython Notebook [Anaconda](http://continuum.io/downloads) in Windows, be sure to use "python setup.py install" using the Anaconda Command Prompt in Windows.
If not, module will be installed for System path python but won't work in the environment of Anaconda IPython Notebook.

#Using pyhaystack
##Open a session with Haystack server

	:::python
		import pyhaystack as ph
		import pandas as pd
		import numpy as np
		# if using Notebook, will allow graph to be inserted directly in the notebook
		%matplotlib inline
		import matplotlib.pyplot as plt
		import re
		session = ph.NiagaraAXConnection('http://serverIP/','user','password')

#Fetching data

##Call list of histories

	:::python
		hisList = session.hisAll()

##Get some trend records as list

	:::python
		trends = session.hisRead(AND_search=['S-3','OA'], start='2014-10-10',end='2014-10-12')

# Use pandas to analyse data
##Compute mean by hour of one record

	:::python
		trends[0].data.resample('h')

##Plot a beautiful graph

	:::python
		trends[0].plot()
   
##Get some simple stats info on records
	
	:::python
		trends[0].simpleStats()

##Draw a distribution plots (count number of record between 20-20.5, between 20,5-21, etc...

	:::python
		trends[0].breakdownPlot()

![breakdownplot.jpg](https://bitbucket.org/repo/Anyjky/images/859471603-breakdownplot.jpg)