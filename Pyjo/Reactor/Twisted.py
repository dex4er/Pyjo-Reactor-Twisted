"""
Pyjo.Reactor.Twisted - Low-level event reactor with Twisted support
===================================================================
::

    from Pyjo.Reactor.Twisted import Twisted

    # Watch if handle becomes readable or writable
    reactor = Twisted()
    reactor.io(first, lambda reactor, writable: print(
        'First handle is writable' if writable else 'First handle is readable'
    ))

    # Or import the module, as in Google Python Style Guide

    import Pyjo.Reactor.Twisted

    # Watch if handle becomes readable or writable
    reactor = Pyjo.Reactor.Twisted.new()
    reactor.io(first, lambda reactor, writable: print(
        'First handle is writable' if writable else 'First handle is readable'
    ))

    # Change to watching only if handle becomes writable
    reactor.watch(first, False, True)

    # Watch a file descriptor if it becomes readable
    reactor.io(fd, lambda reactor, writable: print(
        'Second handle is writable' if writable else 'Second handle is readable'
    )).watch(fd, True, False)

    # Add a timer
    def timeout(reactor):
        reactor.remove(first)
        reactor.remove(fd)
        print('Timeout!')

    reactor.timer(15, timeout)

    # Start reactor if necessary
    if not reactor.is_running:
        reactor.start()

:mod:`Pyjo.Reactor.Twisted` is a low-level event reactor based on the reactor
of `Twisted <https://twisted.org>`_, the one that the application installed
before, or else the reactor of poll of Twisted, or of select where there is no
poll or it does not work well, as on macOS. Its default on Linux, the reactor
of epoll, is not installed, as epoll keeps its state in the kernel: a socket
that is closed before it is removed leaves it, which Pyjoyment does, and the
state is shared with the child of a fork, as a worker of
:mod:`Pyjo.Server.Prefork`, so an application that installs it has neither.
An application of Twisted that imports ``twisted.internet.reactor`` itself
calls :func:`install` before, which installs the one of poll or select.
``PYJO_REACTOR`` selects it for :mod:`Pyjo.IOLoop`::

    PYJO_REACTOR=Pyjo.Reactor.Twisted

The reactor of Twisted is unique in a process, so only one object of this
class uses it at a time, and :meth:`~Pyjo_Reactor_Twisted.new` returns a
:mod:`Pyjo.Reactor.Poll` object while it lives, as the constructor of the
class does. It runs in the thread that
made it, so the threads of :mod:`Pyjo.Server.Prethread` get
:mod:`Pyjo.Reactor.Poll` objects. When the reactor of Twisted is running
already, as under ``twistd`` or Scrapy, :meth:`~Pyjo_Reactor_Twisted.start`
and :meth:`~Pyjo_Reactor_Twisted.one_tick` return right away, and the events
are handled by the reactor of Twisted that runs.

Events
------

:mod:`Pyjo.Reactor.Twisted` inherits all events from :mod:`Pyjo.Reactor.Poll`.

See also
--------

:mod:`Pyjo.Reactor.Poll`, :mod:`Pyjoyment`, https://github.com/dex4er/Pyjoyment.

Classes
-------
"""

import Pyjo.Exception
import Pyjo.Reactor
import Pyjo.Reactor.Poll

from Pyjo.Reactor import Handle, IOCallback, TimerCallback

import os
import select
import sys
import threading
import weakref

from collections.abc import Callable
from typing import Any, Self, TypedDict

from twisted.internet.interfaces import IReadDescriptor, IWriteDescriptor

# zope.interface has no stubs, as Twisted uses it
from zope.interface import implementer  # pyright: ignore[reportMissingTypeStubs]


__version__ = '0.1.0'

# The object that uses the reactor of Twisted, which is unique, as Mojo::Reactor::EV counts the objects of EV
_active: 'weakref.ref[Pyjo_Reactor_Twisted] | None' = None


class _Timer(TypedDict):
    cb: TimerCallback | None
    after: float
    recurring: bool
    call: Any
    fire: Callable[[], None]


class Pyjo_Reactor_Twisted(Pyjo.Reactor.Poll.object):
    """
    :mod:`Pyjo.Reactor.Twisted` inherits all methods from
    :mod:`Pyjo.Reactor.Poll` and implements the following new ones.
    """

    _timers: dict[str, _Timer]  # pyright: ignore[reportIncompatibleVariableOverride]

    # We have to fall back to Pyjo.Reactor.Poll, since the reactor of Twisted is unique; in the constructor of the class,
    # as new and the constructor make the same object, and Python does not call __init__ for an object of another class
    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        if _active is not None and _active() is not None:
            return Pyjo.Reactor.Poll.new(*args, **kwargs)
        return super().__new__(cls)

    @classmethod
    def new(cls, *args: Any, **kwargs: Any) -> Any:  # pyright: ignore[reportIncompatibleMethodOverride]
        """::

            reactor = Pyjo.Reactor.Twisted.new()

        Construct a new :mod:`Pyjo.Reactor.Twisted` object, or a
        :mod:`Pyjo.Reactor.Poll` object while another one uses the reactor of
        Twisted.
        """
        return cls(*args, **kwargs)

    def __init__(self) -> None:
        global _active
        super().__init__()
        # The reactor that the application installed, or one of poll or select, which keep their state in the process
        install()
        from twisted.internet import reactor

        self._twisted: Any = reactor
        self._descriptors: dict[int, _Descriptor] = {}
        self._ticks = 0
        self._timers = {}  # pyright: ignore[reportIncompatibleVariableOverride]
        _active = weakref.ref(self)
        weakref.finalize(self, _release, reactor, self._descriptors, self._timers)

    def again(self, id: str, after: float | None = None) -> None:
        """::

            reactor.again(id)
            reactor.again(id, 0.5)

        Restart timer and optionally change the invocation time. Note that this
        method requires an active timer.
        """
        if (timer := self._timers.get(id)) is None:
            Pyjo.Exception.object.throw('Timer not active')
        if after is not None:
            timer['after'] = after
        if (call := timer['call']).active():
            call.reset(timer['after'])
        else:
            timer['call'] = self._twisted.callLater(timer['after'], timer['fire'])

    def io(self, handle: Handle, cb: IOCallback) -> Self:
        """::

            reactor = reactor.io(handle, cb)

        Watch handle for I/O events, invoking the callback whenever handle
        becomes readable or writable.
        """
        fd = _fileno(handle)
        self._unwatch(fd)
        self._io[fd] = {'cb': cb, 'mode': 0}
        self._descriptors[fd] = _Descriptor(weakref.ref(self), fd)
        return self.watch(handle, True, True)

    def one_tick(self) -> None:
        """::

            reactor.one_tick()

        Run reactor until an event occurs or no events are being watched
        anymore, or return right away while the reactor of Twisted runs.
        """
        twisted = self._twisted
        if twisted.running:
            return

        running = self._running
        if not running:
            self._running = 1

        try:
            ticks = self._ticks
            while self._ticks == ticks and self._running:
                # The cleanups that finalizers deferred, before the reactor waits
                if Pyjo.Reactor._DEFERRED.get(threading.get_ident()):  # pyright: ignore[reportPrivateUsage]
                    Pyjo.Reactor._drain()  # pyright: ignore[reportPrivateUsage]

                # Stop automatically if there is nothing to watch
                if not len(self._timers) and not len(self._io):
                    return self.stop()

                # I/O, at most until the next timer or for half a second, then the timers that are due, as the reactor of
                # poll has them
                timeout = twisted.timeout()
                twisted.doIteration(0.5 if timeout is None else min(timeout, 0.5))
                twisted.runUntilCurrent()
        finally:
            if not running:
                self._running = running

    def recurring(self, after: float, cb: TimerCallback) -> str:
        """::

            id = reactor.recurring(0.25, cb)

        Create a new recurring timer, invoking the callback repeatedly after a
        given amount of time in seconds.
        """
        return self._timer(True, after, cb)

    def remove(self, remove: Handle | str) -> bool:
        """::

            boolean = reactor.remove(handle)
            boolean = reactor.remove(id)

        Remove handle or timer.
        """
        if isinstance(remove, str):
            if (timer := self._timers.pop(remove, None)) is None:
                return False
            _cancel(timer['call'])
            return True
        fd = _fileno(remove)
        if self._io.pop(fd, None) is None:
            return False
        self._unwatch(fd)
        return True

    def reset(self) -> None:
        """::

            reactor.reset()

        Remove all handles and timers.
        """
        _release(self._twisted, self._descriptors, self._timers)
        self._events = {}
        self._io = {}
        self._next_tick = []
        self._next_timer = None
        self._running = 0

    def start(self) -> None:
        """::

            reactor.start()

        Start watching for I/O and timer events, this will block until
        :meth:`stop` is called or no events are being watched anymore, or
        return right away while the reactor of Twisted runs.
        """
        if self._twisted.running:
            return
        super().start()

    def timer(self, after: float, cb: TimerCallback) -> str:
        """::

            id = reactor.timer(0.5, cb)

        Create a new timer, invoking the callback after a given amount of time
        in seconds.
        """
        return self._timer(False, after, cb)

    def watch(self, handle: Handle, read: bool, write: bool) -> Self:
        """::

            reactor = reactor.watch(handle, readable, writable)

        Change I/O events to watch handle for with true and false values. Note
        that this method requires an active I/O watcher.
        """
        fd = _fileno(handle)
        if fd not in self._io or (descriptor := self._descriptors.get(fd)) is None:
            Pyjo.Exception.object.throw('I/O watcher not active')
        twisted = self._twisted
        if read and not descriptor.reading:
            twisted.addReader(descriptor)
        elif not read and descriptor.reading:
            twisted.removeReader(descriptor)
        if write and not descriptor.writing:
            twisted.addWriter(descriptor)
        elif not write and descriptor.writing:
            twisted.removeWriter(descriptor)
        descriptor.reading, descriptor.writing = read, write
        return self

    def _fire(self, fd: int, writable: bool) -> None:
        if (io := self._io.get(fd)) is None:
            return
        self._ticks += 1
        self._try('I/O watcher', io['cb'], writable)

    def _timer(self, recurring: bool, after: float, cb: TimerCallback) -> str:
        id = self._id()
        ref = weakref.ref(self)

        # The call of Twisted refers to the reactor weakly, as the reactor of Twisted lives as long as the process, and a
        # recurring timer takes the function from the timer, as a reference to itself would make a cycle, which keeps the
        # callback until the garbage collector runs
        def fire() -> None:
            if (reactor := ref()) is None or (timer := reactor._timers.get(id)) is None:
                return
            if timer['recurring']:
                timer['call'] = reactor._twisted.callLater(timer['after'], timer['fire'])
            else:
                del reactor._timers[id]
            reactor._ticks += 1
            reactor._try('Timer', cb)

        self._timers[id] = {
            'cb': cb,
            'after': after,
            'recurring': recurring,
            'call': self._twisted.callLater(after, fire),
            'fire': fire,
        }
        return id

    def _unwatch(self, fd: int) -> None:
        if (descriptor := self._descriptors.pop(fd, None)) is not None:
            _unwatch(self._twisted, descriptor)

    def _wake(self) -> None:
        self._twisted.callFromThread(lambda: None)


# A handle of the reactor of Twisted, which calls the I/O watcher of its file descriptor; the decorator of zope.interface
# has no types
@implementer(IReadDescriptor, IWriteDescriptor)  # pyright: ignore[reportUntypedClassDecorator]
class _Descriptor:
    def __init__(self, reactor: 'weakref.ref[Pyjo_Reactor_Twisted]', fd: int) -> None:
        self.fd = fd
        self.reactor = reactor
        self.reading = self.writing = False

    # The reactor of Twisted removes the handle at a hang-up or an error without data, as the refusal of a connection,
    # where the reactor of poll calls the watcher, which finds the error of the socket, so the watcher is called as the
    # handle was watched, readable and writable
    def connectionLost(self, reason: Any) -> None:
        reading, writing = self.reading, self.writing
        self.reading = self.writing = False
        if (reactor := self.reactor()) is None:
            return
        if reading:
            reactor._fire(self.fd, False)  # pyright: ignore[reportPrivateUsage]
        if writing and reactor._descriptors.get(self.fd) is self:  # pyright: ignore[reportPrivateUsage]
            reactor._fire(self.fd, True)  # pyright: ignore[reportPrivateUsage]

    def doRead(self) -> None:
        if (reactor := self.reactor()) is not None:
            reactor._fire(self.fd, False)  # pyright: ignore[reportPrivateUsage]

    def doWrite(self) -> None:
        if (reactor := self.reactor()) is not None:
            reactor._fire(self.fd, True)  # pyright: ignore[reportPrivateUsage]

    def fileno(self) -> int:
        return self.fd

    def logPrefix(self) -> str:
        return 'Pyjo.Reactor.Twisted'


# The child of a fork has the waker of the parent, the pipe that wakes the reactor of Twisted from other threads, whose
# wake-ups the parent and the child would read from each other, so the child gets one of its own
def _after_fork_in_child() -> None:
    if _active is None or (reactor := _active()) is None:
        return
    twisted = reactor._twisted  # pyright: ignore[reportPrivateUsage]
    if (waker := getattr(twisted, 'waker', None)) is None:
        return
    twisted._removeInternalReader(waker)
    waker.connectionLost(None)
    twisted.waker = None
    twisted.installWaker()


def _cancel(call: Any) -> None:
    if call.active():
        call.cancel()


def _fileno(handle: Handle) -> int:
    fd = handle if isinstance(handle, int) else handle.fileno()
    if fd < 0:
        Pyjo.Exception.object.throw('Handle is closed')
    return fd


# The reactor of poll, or of select where there is no poll or it does not work well, as on macOS, which Twisted itself
# prefers to poll there, in the place of the default of Twisted, which is epoll on Linux
def install() -> None:
    """::

        Pyjo.Reactor.Twisted.install()

    Install the reactor of Twisted that :mod:`Pyjo.Reactor.Twisted` prefers,
    of poll, or of select where there is no poll or it does not work well, as
    on macOS, in the place of the default of Twisted, epoll on Linux. An
    application of Twisted calls it before it imports
    ``twisted.internet.reactor``, which installs the default. It does nothing
    where a reactor of Twisted is installed already. ::

        import Pyjo.Reactor.Twisted

        Pyjo.Reactor.Twisted.install()

        from twisted.internet import reactor
    """
    if 'twisted.internet.reactor' in sys.modules:
        return
    if sys.platform != 'darwin' and hasattr(select, 'poll'):
        from twisted.internet import pollreactor

        pollreactor.install()
    else:
        from twisted.internet import selectreactor

        selectreactor.install()


# The handles and the calls that an object leaves in the reactor of Twisted, at a reset and when it is freed
def _release(twisted: Any, descriptors: dict[int, _Descriptor], timers: dict[str, _Timer]) -> None:
    for descriptor in descriptors.values():
        _unwatch(twisted, descriptor)
    descriptors.clear()
    for timer in timers.values():
        _cancel(timer['call'])
    timers.clear()


def _unwatch(twisted: Any, descriptor: _Descriptor) -> None:
    if descriptor.reading:
        twisted.removeReader(descriptor)
    if descriptor.writing:
        twisted.removeWriter(descriptor)
    descriptor.reading = descriptor.writing = False


if hasattr(os, 'register_at_fork'):
    os.register_at_fork(after_in_child=_after_fork_in_child)

new = Pyjo_Reactor_Twisted.new
object = Pyjo_Reactor_Twisted
Twisted = Pyjo_Reactor_Twisted
