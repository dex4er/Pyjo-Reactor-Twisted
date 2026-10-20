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
- Unless the application installed a reactor of Twisted, it installs the one of
  poll, or of select on macOS and where there is no poll, not epoll, the
  default of Twisted on Linux: epoll keeps its state in the kernel, which drops
  a socket that Pyjoyment closes before it removes it, so that the removal
  fails and Twisted keeps the number of the descriptor for the next socket,
  and which the child of a fork, as a worker of `Pyjo.Server.Prefork`, shares
  with its parent. The child gets a waker of its own.
- The reactor of Twisted removes a handle at a hang-up or an error without
  data, as a refused connection, and tells only `connectionLost`, where the
  reactor of poll calls the watcher, which finds the error of the socket and
  tries the next address, so `connectionLost` calls the watcher as the handle
  was watched. macOS hides both, as the reactor of select reports such a socket
  as writable: CI runs on Linux.
- The callbacks that the reactor of Twisted keeps refer to the object weakly,
  as the reactor of Twisted lives as long as the process; a finalizer removes
  the descriptors and cancels the calls of an object that is freed.

## Development

The distribution depends on Pyjoyment of its Git repository, as the revival
of Pyjoyment is not on PyPI yet (`[tool.uv.sources]` of `pyproject.toml`). A
path to the checkout next to this one cannot be the source: uv applies the
sources of a dependency of Git, so whoever installs the reactor from Git would
get a subdirectory of this repository that does not exist. The tests lay the
checkout next to this one over it with `--with-editable`, so that they test
what is there:

```sh
mise exec -- uv sync
mise exec -- uv run --with-editable ../Pyjoyment python -m Pyjo.Prove -l -r t
```

Perl's `prove` runs them too, with `.proverc`, under `uv run`, whose `python`
is the one of the environment, where Pyjoyment and the reactor are installed,
so that it needs no `PYTHONPATH`, unlike in Pyjoyment:

```sh
mise exec -- uv run --with-editable ../Pyjoyment prove -r t
```

The tests of Pyjoyment run on this reactor as well, with `PYJO_REACTOR`:

```sh
cd ../Pyjoyment
PYJO_REACTOR=Pyjo.Reactor.Twisted mise exec -- uv run --project ../Pyjo-Reactor-Twisted --with-editable . \
  python -m Pyjo.Prove -l -j 4 -r t
```

Trunk checks the files with the linters of Pyjoyment, from `.trunk/trunk.yaml`:

```sh
trunk check --all
```

Its pyright needs the environment of `uv sync`, `.venv`, which `tool.pyright` of
`pyproject.toml` names, as the reactor imports Pyjoyment and Twisted, while
Pyjoyment has no dependencies to find; Trunk Check of CI runs `uv sync` first.
The examples and the tests are not checked by pyright: for them it takes the
regular package `Pyjo` of Pyjoyment, which hides `Pyjo.Reactor.Twisted` of the
checkout.

`t/Reactor_Twisted.py` is the port of `t/mojo/reactor_ev.t` of Mojolicious
9.49, from `t/Pyjo/Reactor_Poll.py` of Pyjoyment, with the differences of
`reactor_ev.t`.
