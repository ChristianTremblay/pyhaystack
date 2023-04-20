Signal/Slot design pattern
~~~~~~~~~~~~~~~~~~~~~~~~~~

Introduction
============

Signal/Slot is a pattern that allows loose coupling various components of a
software without having to introduce boilerplate code. Loose coupling of
components allows better modularity in software code which has the nice side
effect of making it easier to test because less dependencies means less mocking
and monkey patching.

Signal/Slot is a widely used pattern, many frameworks have it built-in
including Django, Qt and probably many others. If you have a standalone project
then you probably don't want to add a big dependency like PyQt or Django just
for a Signal/Slot framework. There are a couple of standalone libraries which
allow to acheive a similar result, like Circuits or PyPubSub,  which has way
more features than ``signalslots``, like messaging over the network and is a
quite complicated and has weird (non-PyPi hosted) dependencies and is not PEP8
compliant ...

``signalslot`` has the vocation of being a light and simple implementation of
the well known Signal/Slot design pattern provided as a classic quality Python
package.

Tight coupling
==============

Consider such a code in ``your_client.py``:

.. code-block:: python

    import your_service
    import your_dirty_hack  # WTH is that doing here ? huh ?

    class YourClient(object):
        def something_happens(self, some_argument):
            your_service.something_happens(some_argument)
            your_dirty_hack.something_happens(some_argument)

The problem with that code is that it ties ``your_client`` with
``your_service`` and ``your_dirty_hack`` which you really didn't want to put
there, but had to, "until you find a better place for it".

Tight coupling makes code harder to test because it takes more mocking and
harder to maintain because it has more dependencies.

An improvement would be to acheive the same while keeping components loosely
coupled.

Observer pattern
================

You could implement an Observer pattern in ``YourClient`` by adding
boilerplate code:

.. code-block:: python

    class YourClient(object):
        def __init__(self):
            self.observers = []

        def register_observer(self, observer):
            self.observers.append(observer)

        def something_happens(self, some_argument):
            for observer in self.observers:
                observer.something_happens(some_argument)

This implementation is a bit dumb, it doesn't check the compatibility of
observers for example, also it's additionnal code you'd have to test, and it's
"boilerplate".

This would work if you have control on instanciation of ``YourClient``, ie.:

.. code-block:: python

    your_client = YourClient()
    your_client.register_observer(your_service)
    your_client.register_observer(your_dirty_hack)

If ``YourClient`` is used by a framework with `IoC
<http://en.wikipedia.org/wiki/Inversion_of_control>`_ then it might become
harder:

.. code-block:: python

    service = some_framework.Service.create(
        client='your_client.YourClient')

    service._client.register_observer(your_service)
    service._client.register_observer(your_dirty_hack)

In this example, we're accessing a private python variable ``_client`` and
that's never very good because it's not safe against forward compatibility.

With Signal/Slot
================

Using the Signal/Slot pattern, the same result could be achieved with total
component decoupling. It would organise as such:

- ``YourClient`` defines a ``something_happens`` signal,
- ``your_service`` connects its own callback to the ``something_happens``,
- so does ``your_dirty_hack``,
- ``YourClient.something_happens()`` "emits" a signal, which in turn calls all
  connected callbacks.

Note that a connected callback is called a "slot" in the "Signal/Slot" pattern.

See :doc:`usage` for example code.
