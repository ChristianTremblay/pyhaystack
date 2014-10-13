For this to work with Anaconda IPython Notebook in Windows, be sure to use "python setup.py install" using the Anaconda Command Prompt in Windows.
If not, module will be installed for System path python but won't work in the environment of Anaconda IPython Notebook.

Opening a session

import pyhaystack as ph
import pandas as pd
import numpy as np
%matplotlib inline
import matplotlib.pyplot as plt
import re

# Open a session with Haystack server
session = ph.NiagaraAXConnection('http://serverIP/','user','password')

Fetching data

# Call list of histories
hisList = session.hisAll()

#get a list of trends
trends = session.hisRead(AND_search=['S-3','OA'], start='2014-10-10',end='2014-10-12')

# Compute mean by hour
trends[0].data.resample('h')

# Plot a beautiful graph
trends[0].plot()
   