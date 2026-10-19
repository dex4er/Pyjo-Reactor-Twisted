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

## Status

An experiment: the first reactor of Pyjoyment in a distribution of its own.

## License

The Artistic License 2.0, as Pyjoyment.
