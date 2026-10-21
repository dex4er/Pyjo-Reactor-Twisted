import os


# Unlike Mojolicious: the reactor of the test is selected before Pyjo.IOLoop is loaded, as Mojo::Reactor->detect prefers
# Mojo::Reactor::EV where it is installed, and Pyjo.Reactor.detect() prefers Pyjo.Reactor.Asyncio
os.environ['PYJO_REACTOR'] = 'Pyjo.Reactor.Twisted'

import Pyjo.Reactor  # noqa: E402
import Pyjo.Reactor.Poll  # noqa: E402
import Pyjo.Reactor.Twisted  # noqa: E402

from Pyjo.Loader import load_class  # noqa: E402
from Pyjo.Test import *  # noqa: E402

import gc  # noqa: E402
import socket  # noqa: E402
import time  # noqa: E402


def eval_(cb):
    try:
        cb()
    except Exception as e:
        return e


readable = writable = 0


def rw_cb(reactor, is_writable):
    global readable, writable
    if is_writable:
        writable += 1
    else:
        readable += 1


# Instantiation
reactor = Pyjo.Reactor.Twisted.new()
is_ok(type(reactor), Pyjo.Reactor.Twisted.object, 'right object')
is_ok(type(Pyjo.Reactor.Twisted.new()), Pyjo.Reactor.Poll.object, 'right object')
del reactor
# Not in Mojolicious: the garbage collector runs, as PyPy frees the reactor only then, where Perl frees it at once
gc.collect()
is_ok(type(Pyjo.Reactor.Twisted.new()), Pyjo.Reactor.Twisted.object, 'right object')
gc.collect()
# Not in Mojolicious: the constructor of Python, which falls back to Pyjo.Reactor.Poll as new does
is_ok(Pyjo.Reactor.Twisted.Twisted, Pyjo.Reactor.Twisted.object, 'right class')
reactor = Pyjo.Reactor.Twisted.Twisted()
is_ok(type(reactor), Pyjo.Reactor.Twisted.object, 'right object')
is_ok(type(Pyjo.Reactor.Twisted.Twisted()), Pyjo.Reactor.Poll.object, 'right object')
is_ok(type(Pyjo.Reactor.Twisted.new()), Pyjo.Reactor.Poll.object, 'right object')
del reactor
gc.collect()
is_ok(type(Pyjo.Reactor.Twisted.Twisted()), Pyjo.Reactor.Twisted.object, 'right object')
gc.collect()
ok(not load_class('Pyjo.IOLoop'), 'use Pyjo.IOLoop')
reactor = Pyjo.IOLoop.singleton.reactor
is_ok(type(reactor), Pyjo.Reactor.Twisted.object, 'right object')

# Make sure it stops automatically when not watching for events
triggered = 0


def triggered_cb(loop):
    global triggered
    triggered += 1


Pyjo.IOLoop.next_tick(triggered_cb)
Pyjo.IOLoop.start()
ok(triggered, 'reactor waited for one event')
started = time.time()
Pyjo.IOLoop.start()
Pyjo.IOLoop.one_tick()
ok(time.time() < (started + 10), 'stopped automatically')

# Listen
listen = socket.create_server(('127.0.0.1', 0), backlog=5)
port = listen.getsockname()[1]
reactor.io(listen, rw_cb).watch(listen, False, False).watch(listen, True, True)
reactor.timer(0.025, lambda reactor: reactor.stop())
reactor.start()
ok(not readable, 'handle is not readable')
ok(not writable, 'handle is not writable')

# Connect
client = socket.create_connection(('127.0.0.1', port))
reactor.timer(1, lambda reactor: reactor.stop())
reactor.start()
ok(readable, 'handle is readable')
ok(not writable, 'handle is not writable')

# Accept
server = listen.accept()[0]
ok(reactor.remove(listen), 'removed')
ok(not reactor.remove(listen), 'not removed again')
readable = writable = 0
reactor.io(client, rw_cb)
reactor.again(reactor.timer(0.025, lambda reactor: reactor.stop()))
reactor.start()
ok(not readable, 'handle is not readable')
ok(writable, 'handle is writable')
client.sendall(b'hello!\n')
time.sleep(1)
ok(reactor.remove(client), 'removed')
readable = writable = 0
reactor.io(server, rw_cb)
reactor.watch(server, True, False)
reactor.timer(0.025, lambda reactor: reactor.stop())
reactor.start()
ok(readable, 'handle is readable')
ok(not writable, 'handle is not writable')
readable = writable = 0
reactor.watch(server, True, True)
reactor.timer(0.025, lambda reactor: reactor.stop())
reactor.start()
ok(readable, 'handle is readable')
ok(writable, 'handle is writable')
readable = writable = 0
reactor.watch(server, False, False)
reactor.timer(0.025, lambda reactor: reactor.stop())
reactor.start()
ok(not readable, 'handle is not readable')
ok(not writable, 'handle is not writable')
readable = writable = 0
reactor.watch(server, True, False)
reactor.timer(0.025, lambda reactor: reactor.stop())
reactor.start()
ok(readable, 'handle is readable')
ok(not writable, 'handle is not writable')
readable = writable = 0
reactor.io(server, rw_cb)
reactor.timer(0.025, lambda reactor: reactor.stop())
reactor.start()
ok(readable, 'handle is readable')
ok(writable, 'handle is writable')

# Timers
timer = recurring = 0


def timer_cb(reactor):
    global timer
    timer += 1


def recurring_cb(reactor):
    global recurring
    recurring += 1


reactor.timer(0, timer_cb)
ok(reactor.remove(reactor.timer(0, timer_cb)), 'removed')
id = reactor.recurring(0, recurring_cb)
readable = writable = 0
reactor.timer(0.025, lambda reactor: reactor.stop())
reactor.start()
ok(readable, 'handle is readable again')
ok(writable, 'handle is writable again')
ok(timer, 'timer was triggered')
ok(recurring, 'recurring was triggered')
done = False
readable = writable = timer = recurring = 0


def done_cb(reactor):
    global done
    done = reactor.is_running


reactor.timer(0.025, done_cb)
while not done:
    reactor.one_tick()
ok(readable, 'handle is readable again')
ok(writable, 'handle is writable again')
ok(not timer, 'timer was not triggered')
ok(recurring, 'recurring was triggered again')
readable = writable = timer = recurring = 0
reactor.timer(0.025, lambda reactor: reactor.stop())
reactor.start()
ok(readable, 'handle is readable again')
ok(writable, 'handle is writable again')
ok(not timer, 'timer was not triggered')
ok(recurring, 'recurring was triggered again')
ok(reactor.remove(id), 'removed')
ok(not reactor.remove(id), 'not removed again')
readable = writable = timer = recurring = 0
reactor.timer(0.025, lambda reactor: reactor.stop())
reactor.start()
ok(readable, 'handle is readable again')
ok(writable, 'handle is writable again')
ok(not timer, 'timer was not triggered')
ok(not recurring, 'recurring was not triggered again')
readable = writable = timer = recurring = 0
next_tick = 0


def next_tick_cb(reactor):
    global next_tick
    next_tick += 1


is_ok(reactor.next_tick(next_tick_cb), None, 'returned None')
id = reactor.recurring(0, recurring_cb)
reactor.timer(0.025, lambda reactor: reactor.stop())
reactor.start()
ok(readable, 'handle is readable again')
ok(writable, 'handle is writable again')
ok(not timer, 'timer was not triggered')
ok(recurring, 'recurring was triggered again')
ok(next_tick, 'next tick was triggered')


# Reset
def reset_failed_cb(reactor):
    raise Exception('Reset failed')


reactor.next_tick(reset_failed_cb)
reactor.reset()
readable = writable = recurring = 0
reactor.next_tick(lambda reactor: reactor.stop())
reactor.start()
ok(not readable, 'io event was not triggered again')
ok(not writable, 'io event was not triggered again')
ok(not recurring, 'recurring was not triggered again')
reactor2 = Pyjo.Reactor.Twisted.new()
is_ok(type(reactor2), Pyjo.Reactor.Poll.object, 'right object')

# Ordered next_tick
result = []
for i in range(1, 11):
    reactor.next_tick(lambda reactor, i=i: result.append(i))
reactor.start()
is_deeply_ok(result, list(range(1, 11)), 'right result')

# Reset while watchers are active
writable = 0


def reset_cb(reactor, is_writable):
    global writable
    writable += 1
    reactor.reset()


for handle in (client, server):
    reactor.io(handle, reset_cb).watch(handle, False, True)
reactor.start()
is_ok(writable, 1, 'only one handle was writable')
client.close()
server.close()

# Concurrent reactors
timer = 0
reactor.recurring(0, timer_cb)
timer2 = 0


def timer2_cb(reactor):
    global timer2
    timer2 += 1


reactor2.recurring(0, timer2_cb)
reactor.timer(0.025, lambda reactor: reactor.stop())
reactor.start()
ok(timer, 'timer was triggered')
ok(not timer2, 'timer was not triggered')
timer = timer2 = 0
reactor2.timer(0.025, lambda reactor: reactor.stop())
reactor2.start()
ok(not timer, 'timer was not triggered')
ok(timer2, 'timer was triggered')
timer = timer2 = 0
reactor.timer(0.025, lambda reactor: reactor.stop())
reactor.start()
ok(timer, 'timer was triggered')
ok(not timer2, 'timer was not triggered')
timer = timer2 = 0
reactor2.timer(0.025, lambda reactor: reactor.stop())
reactor2.start()
ok(not timer, 'timer was not triggered')
ok(timer2, 'timer was triggered')
reactor.reset()

# Restart timer
single = pair = last = 0


def single_cb(reactor):
    global single
    single += 1


def one_cb(reactor):
    global pair, last
    if single and pair:
        last += 1
    pair += 1
    reactor.stop() if pair > 1 else reactor.again(two)


def two_cb(reactor):
    global pair, last
    if single and pair:
        last += 1
    pair += 1
    reactor.stop() if pair > 1 else reactor.again(one)


reactor.timer(0.025, single_cb)
one = reactor.timer(0.025, one_cb)
two = reactor.timer(0.025, two_cb)
reactor.start()
is_ok(pair, 2, 'timer pair was triggered')
ok(single, 'single timer was triggered')
ok(last, 'timers were triggered in the right order')

# Reset timer
before = time.monotonic()
after = None
again = 0


def after_cb(reactor):
    global after
    after = time.monotonic()


def again_cb(reactor):
    global again
    again += 1
    if again > 3:
        reactor.remove(two)


def restart_cb(reactor):
    reactor.again(one, 0.025)
    reactor.again(two, 0.025)


one = reactor.timer(300, after_cb)
two = reactor.recurring(300, again_cb)
reactor.timer(0.025, restart_cb)
reactor.start()
ok(after, 'timer was triggered')
ok((after - before) < 200, 'less than 200 seconds')
is_ok(again, 4, 'recurring timer triggered four times')

# Restart inactive timer
id = reactor.timer(0, lambda reactor: None)
ok(reactor.remove(id), 'removed')
err = eval_(lambda: reactor.again(id))
like_ok(str(err), r'Timer not active', 'right error')

# Change inactive I/O watcher
ok(not reactor.remove(listen), 'not removed again')
err = eval_(lambda: reactor.watch(listen, True, True))
like_ok(str(err), r'I/O watcher not active', 'right error')
listen.close()

# Error
err = None


def error_cb(reactor, e):
    global err
    reactor.stop()
    err = e


def die_cb(reactor):
    raise Exception('works!\n')


reactor.unsubscribe('error').on('error', error_cb)
reactor.timer(0, die_cb)
reactor.start()
like_ok(str(err), r'works!', 'right error')

# Reset events
reactor.on('error', lambda reactor, err: None)
ok(reactor.has_subscribers('error'), 'has subscribers')
reactor.reset()
ok(not reactor.has_subscribers('error'), 'no subscribers')

# Recursion
timer = 0


def recursion_cb(reactor):
    global timer
    timer += 1
    reactor.one_tick()


reactor = reactor.new()
reactor.timer(0, recursion_cb)
reactor.one_tick()
is_ok(timer, 1, 'timer was triggered once')

# Detection
is_ok(Pyjo.Reactor.object.detect(), 'Pyjo.Reactor.Twisted', 'right class')

# Reactor in control
is_ok(type(Pyjo.IOLoop.singleton.reactor), Pyjo.Reactor.Twisted.object, 'right object')
ok(not Pyjo.IOLoop.is_running(), 'loop is not running')
buffer = b''
server_err = server_running = client_err = client_running = None


def server_cb(loop, stream, cid):
    global server_err, server_running
    stream.write(b'test', lambda stream: stream.write(b'321'))
    server_running = Pyjo.IOLoop.is_running()
    server_err = eval_(lambda: Pyjo.IOLoop.start())


id = Pyjo.IOLoop.server(server_cb, address='127.0.0.1')
port = Pyjo.IOLoop.acceptor(id).port


def client_cb(loop, err, stream):
    global client_err, client_running

    def read_cb(stream, chunk):
        global buffer
        buffer += chunk
        if buffer != b'test321':
            return
        Pyjo.IOLoop.singleton.reactor.stop()

    stream.on('read', read_cb)
    client_running = Pyjo.IOLoop.is_running()
    client_err = eval_(lambda: Pyjo.IOLoop.start())


Pyjo.IOLoop.client(client_cb, port=port)
Pyjo.IOLoop.singleton.reactor.start()
ok(not Pyjo.IOLoop.is_running(), 'loop is not running')
like_ok(str(server_err), r'^Pyjo.IOLoop already running', 'right error')
like_ok(str(client_err), r'^Pyjo.IOLoop already running', 'right error')
ok(server_running, 'loop is running')
ok(client_running, 'loop is running')

# Left out from Mojolicious: the abstract methods of Mojo::Reactor, as reactor_ev.t does not have them

done_testing()
