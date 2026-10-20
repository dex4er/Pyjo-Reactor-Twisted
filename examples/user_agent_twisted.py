import os


# The reactor of Pyjoyment on the reactor of Twisted, selected before Pyjo.IOLoop is loaded
os.environ['PYJO_REACTOR'] = 'Pyjo.Reactor.Twisted'

import Pyjo.Reactor.Twisted  # noqa: E402


# The reactor of Twisted of poll or select, before Twisted is imported, which would install its default, epoll on Linux
Pyjo.Reactor.Twisted.install()

import Pyjo.UserAgent  # noqa: E402

from twisted.internet import reactor, task  # noqa: E402
from twisted.web import resource, server  # noqa: E402


# An application of Twisted
class Hello(resource.Resource):
    isLeaf = True

    def render_GET(self, request):
        return b'Hello from Twisted!'


reactor.listenTCP(3000, server.Site(Hello()))

# The user agent of Pyjoyment, which closes its connections at the end of the block
with Pyjo.UserAgent.new() as ua:
    # A request every second, which does not block the reactor of Twisted; a request that the end of the block
    # interrupts gets an error
    def fetch():
        def done(ua, tx):
            print(tx.error['message'] if tx.error else f'{tx.res.code} {tx.res.text}')

        ua.get('http://127.0.0.1:3000/', done)

    task.LoopingCall(fetch).start(1)
    reactor.run()
