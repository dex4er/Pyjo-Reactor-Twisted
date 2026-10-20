import os


# The reactor of Pyjoyment on the reactor of Twisted, selected before Pyjo.IOLoop is loaded
os.environ['PYJO_REACTOR'] = 'Pyjo.Reactor.Twisted'

import Pyjo.Reactor.Twisted  # noqa: E402


# The reactor of Twisted of poll or select, before Twisted is imported, which would install its default, epoll on Linux
Pyjo.Reactor.Twisted.install()

import Pyjo.HelloWorld  # noqa: E402
import Pyjo.Server.Daemon  # noqa: E402

from twisted.internet import reactor  # noqa: E402


# The server of Pyjoyment, which closes its listen sockets at the end of the block
with Pyjo.Server.Daemon.new(app=Pyjo.HelloWorld.new(), listen=['http://*:3000']) as daemon:
    daemon.start()

    # Twisted runs the event loop, with the server of Pyjoyment in it
    reactor.run()
