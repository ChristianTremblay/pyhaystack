Quantity
----------
Quantity is a way to attach a unit to a float value. Created by hszinc it comes
in two flavours : BasicQuantity and PintQuantity

BasicQuantity is a simple parse of the unit read in the result of the haystack request.
Each variable has a value property and a unit property. Which can be used in your analysis.

PintQuantity is an interpretation of value and units as physical quantities with relation between them.

    "Pint is a Python package to define, operate and manipulate physical 
     quantities: the product of a numerical value and a unit of measurement. 
     It allows arithmetic operations between them and conversions from and to 
     different units."
    
     -- Pint_

It will allow for example, simple unit conversion on the spot.


How to configure
~~~~~~~~~~~~~~~~~~~~~~~~~
You choose between Quantities when defining the session.

.. code:: python

    session = NiagaraHaystackSession(uri='http://server', username='user', password='myComplicatedPassword', pint=True)

By default, Pint is not activated.
It's possible to modify the choice dynamically using

.. code:: python

    session.config_pint(False) # or True


Pros and Cons 
~~~~~~~~~~~~~~~~~~~~~~~~~
For analysis tasks, using PintQuantity is a good thing. You can easily convert
between units and keep coherence in your analysis.

.. code:: python

    from pyhaystack import Q_
    temp = Q_(13,'degC')
    temp.to('degF') 

But when it's time to write to a haystack server, things get complicated. Hard
work has been done to convert from haystack units to Pint. The reverse process
is really difficult because of the non-standard nature of units in project-haystack.

Unit database
~~~~~~~~~~~~~~~~~~~~~~~~~
Pyhaystack uses a custom unit dictionnary built at run time. For more details 
about that, please refer to hszinc_ documentation.


Pandas
~~~~~~~~~~~~~~~~~~~~~~~~~
When reading series and DataFrame, value stored inside are not Quantity. We extact 
the value property only. But for each serie, we add Metadata to store the unit
so you know what's behind.    

.. code:: python

    room_temp_serie.meta['units']

.. parsed-literal::

    <UnitsContainer({'degC': 1.0})>

.. _Pint : https://pint.readthedocs.io/

.. _hszinc : https://github.com/vrtsystems/hszinc