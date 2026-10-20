# Pyjo-Reactor-Twisted

Low level event reactor with [Twisted](https://twisted.org) support for
[Pyjoyment](https://github.com/dex4er/Pyjoyment).

`Pyjo.Reactor.Twisted` runs the I/O and the timers of `Pyjo.IOLoop` in the
reactor of Twisted, so that a Pyjoyment application and the code of Twisted
share one event loop.

## Installation

From the Git repository, as neither the reactor nor the revival of Pyjoyment
is on PyPI yet; with uv, Pyjoyment comes from its Git repository too:

```sh
uv add git+https://github.com/dex4er/Pyjo-Reactor-Twisted
```

## Usage

Select the reactor with `PYJO_REACTOR` before `Pyjo.IOLoop` is loaded:

```sh
PYJO_REACTOR=Pyjo.Reactor.Twisted python myapp.py daemon
```

The reactor of Twisted is unique in a process, so only one `Pyjo.IOLoop` uses
it at a time; the others get `Pyjo.Reactor.Poll`. When the reactor of Twisted
is running already, as under `twistd` or Scrapy, `Pyjo.IOLoop.start()` returns
right away and the events are handled by the reactor that runs.

## Examples

`examples/hello_world_twisted.py` runs `Pyjo.HelloWorld` on the server of
Pyjoyment in the event loop that Twisted runs, with `reactor.run()`, in a
`with` block, which closes the listen sockets of the server at its end:

```python
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
```

```console
$ python examples/hello_world_twisted.py
Web application available at http://127.0.0.1:3000
```

```console
$ curl http://127.0.0.1:3000/
Your Pyjo is working!
```

`examples/user_agent_twisted.py` is an application of Twisted, a server of
`twisted.web`, whose timer requests it every second with the user agent of
Pyjoyment, without blocking the reactor of Twisted. The user agent is in a
`with` block, which closes its connections at its end, so the callback shows
the error of a request that it interrupts:

```python
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
```

```console
$ python examples/user_agent_twisted.py
200 Hello from Twisted!
200 Hello from Twisted!
200 Hello from Twisted!
```

`examples/loopback_twisted.py` is a server of Pyjoyment and its user agent on
the reactor of Twisted, a blocking request, which runs the event loop until
the response, and the class of the reactor, which Build checks with the wheel:

```python
import os


# The reactor of Pyjoyment on the reactor of Twisted, selected before Pyjo.IOLoop is loaded
os.environ['PYJO_REACTOR'] = 'Pyjo.Reactor.Twisted'

import Pyjo.HelloWorld  # noqa: E402
import Pyjo.IOLoop  # noqa: E402
import Pyjo.Server.Daemon  # noqa: E402
import Pyjo.UserAgent  # noqa: E402


# The server, on a port that the system picks, and the user agent, in the same event loop, which close their sockets at
# the end of the block
with (
    Pyjo.Server.Daemon.new(app=Pyjo.HelloWorld.new(), listen=['http://127.0.0.1'], silent=True) as daemon,
    Pyjo.UserAgent.new(ioloop=Pyjo.IOLoop.singleton) as ua,
):
    # A blocking request, which runs the event loop of the server on the reactor of Twisted until the response
    tx = ua.get(f'http://127.0.0.1:{daemon.start().ports()[0]}/')
    print(type(Pyjo.IOLoop.singleton.reactor).__name__)
    print(tx.result.code, tx.result.text)
```

```console
$ python examples/loopback_twisted.py
Pyjo_Reactor_Twisted
200 Your Pyjo is working!
```

The first two call `Pyjo.Reactor.Twisted.install()` before they import
Twisted, which would install its default, epoll on Linux, in the place of poll
or select; the third does not import Twisted, so the reactor installs it.

## Status

An experiment: the first reactor of Pyjoyment in a distribution of its own.

## License

The Artistic License 2.0, as Pyjoyment.
