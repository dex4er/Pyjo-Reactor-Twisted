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
`with` block, which closes the listen sockets of the server at its end.

`examples/user_agent_twisted.py` is an application of Twisted, a server of
`twisted.web`, whose timer requests it every second with the user agent of
Pyjoyment, without blocking the reactor of Twisted. The user agent is in a
`with` block, which closes its connections at its end, so the callback shows
the error of a request that it interrupts.

Both call `Pyjo.Reactor.Twisted.install()` before they import Twisted, which
would install its default, epoll on Linux, in the place of poll or select.

## Status

An experiment: the first reactor of Pyjoyment in a distribution of its own.

## License

The Artistic License 2.0, as Pyjoyment.
