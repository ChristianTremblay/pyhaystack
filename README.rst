pyhaystack |build-status| |coverage| |docs| 
===========================================

Pyhaystack is a module that allow python programs to connect to a haystack server [project-haystack.org](http://www.project-haystack.org).

Actually, connection can be established with Niagara Platform running the nhaystack module.

It's a work in progress and actually, main goal is to connect to server and retrive histories to make numeric analysis. Eventually, other options will be implemented through the REST API.

For this to work with [Anaconda](http://continuum.io/downloads) IPython Notebook in Windows, be sure to use "python setup.py install" using the Anaconda Command Prompt in Windows.
If not, module will be installed for System path python but won't work in the environment of Anaconda IPython Notebook.

Chat with us on |Gitter|

.. |build-status| image:: https://travis-ci.org/ChristianTremblay/pyhaystack.svg?branch=master
   :target: https://travis-ci.org/ChristianTremblay/pyhaystack
   :alt: Build status
     
.. |docs| image:: https://readthedocs.org/projects/pyhaystack/badge/?version=latest
   :target: http://pyhaystack.readthedocs.org/
   :alt: Documentation
   
.. |coverage| image:: https://coveralls.io/repos/ChristianTremblay/pyhaystack/badge.svg?branch=master&service=github
   :target: https://coveralls.io/github/ChristianTremblay/pyhaystack?branch=master
   :alt: Coverage
   
.. |Gitter| image:: https://badges.gitter.im/ChristianTremblay/pyhaystack.svg
	:target: https://gitter.im/ChristianTremblay/pyhaystack?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=body_badge
	:alt: Gitter

