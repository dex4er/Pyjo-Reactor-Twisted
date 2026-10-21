.. automodule:: Pyjo.Reactor.Twisted
    :members:

.. The examples follow the API, after the docstring of the module, which ends with its classes: a section here would
   be a second title of the page, as the sections of the docstring are its own.

.. rubric:: Examples
    :heading-level: 2
    :name: examples

``examples/hello_world_twisted.py`` runs ``Pyjo.HelloWorld`` on the server of
Pyjoyment in the event loop that Twisted runs, with ``reactor.run()``, in a
``with`` block, which closes the listen sockets of the server at its end:

    .. include:: ../examples/hello_world_twisted.py
       :code: python

.. code-block:: console

    $ python examples/hello_world_twisted.py
    Web application available at http://127.0.0.1:3000

.. code-block:: console

    $ curl http://127.0.0.1:3000/
    Your Pyjo is working!

``examples/user_agent_twisted.py`` is an application of Twisted, a server of
``twisted.web``, whose timer requests it every second with the user agent of
Pyjoyment, without blocking the reactor of Twisted. The user agent is in a
``with`` block, which closes its connections at its end, so the callback shows
the error of a request that it interrupts:

    .. include:: ../examples/user_agent_twisted.py
       :code: python

.. code-block:: console

    $ python examples/user_agent_twisted.py
    200 Hello from Twisted!
    200 Hello from Twisted!
    200 Hello from Twisted!

``examples/loopback_twisted.py`` is a server of Pyjoyment and its user agent on
the reactor of Twisted, a blocking request, which runs the event loop until
the response, and the class of the reactor:

    .. include:: ../examples/loopback_twisted.py
       :code: python

.. code-block:: console

    $ python examples/loopback_twisted.py
    Pyjo_Reactor_Twisted
    200 Your Pyjo is working!

The first two call :func:`~Pyjo.Reactor.Twisted.install` before they import
Twisted, which would install its default, epoll on Linux, in the place of poll
or select; the third does not import Twisted, so the reactor installs it.
