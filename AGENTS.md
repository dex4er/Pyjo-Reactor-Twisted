# Agent Guide: Pyjo-Reactor-Twisted

## Overview

`Pyjo.Reactor.Twisted` is a reactor of Pyjoyment on the reactor of Twisted, in
a distribution of its own, as every reactor of Pyjoyment with a dependency is:
Pyjoyment has no runtime dependencies, and one reactor does not pull the
dependencies of another. The conventions are those of Pyjoyment: read its
`AGENTS.md` in the checkout next to this one, `../Pyjoyment/AGENTS.md`.

## How it works

- It is a subclass of `Pyjo.Reactor.Poll`, as `Mojo::Reactor::EV` is of
  `Mojo::Reactor::Poll`: the I/O watchers are descriptors of Twisted
  (`addReader`, `addWriter`), the timers calls of `callLater`.
- The reactor of Twisted is unique in a process, as the default loop of EV, so
  `new()` returns a `Pyjo.Reactor.Poll` object while another object uses it,
  as `Mojo::Reactor::EV->new` does.
- `reactor.run()` of Twisted cannot run a second time, so `one_tick` runs
  `runUntilCurrent()` and one `doIteration()` of Twisted, and `start` repeats
  `one_tick`, as `Pyjo.Reactor.Poll` does. While the reactor of Twisted runs,
  started by something else, both return right away, as
  `Pyjo.Reactor.Asyncio` does in a running loop of asyncio.
- The callbacks that the reactor of Twisted keeps refer to the object weakly,
  as the reactor of Twisted lives as long as the process; a finalizer removes
  the descriptors and cancels the calls of an object that is freed.

## Development

The distribution depends on Pyjoyment of the checkout next to this one, as the
revival of Pyjoyment is not on PyPI yet (`[tool.uv.sources]` of
`pyproject.toml`):

```sh
mise exec -- uv sync
mise exec -- uv run python -m Pyjo.Prove -l -r t
```

Perl's `prove` runs them too, with `.proverc`, under `uv run`, whose `python`
is the one of the environment, where Pyjoyment and the reactor are installed,
so that it needs no `PYTHONPATH`, unlike in Pyjoyment:

```sh
mise exec -- uv run prove -r t
```

The tests of Pyjoyment run on this reactor as well, with `PYJO_REACTOR`:

```sh
cd ../Pyjoyment
PYJO_REACTOR=Pyjo.Reactor.Twisted mise exec -- uv run --project ../Pyjo-Reactor-Twisted \
  python -m Pyjo.Prove -l -j 4 -r t
```

`t/Reactor_Twisted.py` is the port of `t/mojo/reactor_ev.t` of Mojolicious
9.49, from `t/Pyjo/Reactor_Poll.py` of Pyjoyment, with the differences of
`reactor_ev.t`.
