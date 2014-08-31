For this to work with Anaconda IPython Notebook in Windows, be sure to use "python setup.py install" using the Anaconda Command Prompt in Windows.
If not, module will be installed for System path python but won't work in the environment of Anaconda IPython Notebook.

Opening a session

import pyhaystack as ph
session = ph.NiagaraAXConenction(url,username,password)

Fetching data

# Build list of histories
hisList = Histories(session).getListofId()
# Fetch a LOT of data
#recordList = []
#fetchTrendsForToday(session)
# Play with Pandas
#joined = (recordList[0].data).combine_first(recordList[1].data)

# Plot a beautiful graph
#joined.plot()
#recordList[0].data.plot()
   
# GET request examples
# Json format
#prettyprint(session.getJson('read?filter=sensor'))
# Default Zinc format
print session.getZinc('read?filter=sensor')