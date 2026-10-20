from Pyjo.Test import *

import http.client
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time


# The examples, on the port 3000 replaced by a free one, each in a process of its own
EXAMPLES = os.path.join(os.path.dirname(__file__), '..', 'examples')


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def get(port, deadline):
    while True:
        try:
            conn = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
            try:
                conn.request('GET', '/')
                res = conn.getresponse()
                return res.status, res.read()
            finally:
                conn.close()
        except OSError:
            if time.monotonic() > deadline:
                raise
            time.sleep(0.1)


with subtest('hello_world_twisted.py'), tempfile.TemporaryDirectory() as dir:
    with open(os.path.join(EXAMPLES, 'hello_world_twisted.py')) as file:
        source = file.read()
    port = free_port()
    script = os.path.join(dir, 'hello_world_twisted.py')
    with open(script, 'w') as file:
        file.write(source.replace('3000', str(port)))

    process = subprocess.Popen([sys.executable, script], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        status, body = get(port, time.monotonic() + 30)
        is_ok(status, 200, 'right status')
        is_ok(body, b'Your Pyjo is working!', 'right content')
    finally:
        process.send_signal(signal.SIGINT)
        try:
            process.wait(10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        output = process.stdout.read()
        process.stdout.close()
    is_ok(process.returncode, 0, 'stopped by INT')
    like_ok(output, rf'Web application available at http://127\.0\.0\.1:{port}', 'listening')

with subtest('user_agent_twisted.py'), tempfile.TemporaryDirectory() as dir:
    with open(os.path.join(EXAMPLES, 'user_agent_twisted.py')) as file:
        source = file.read()
    port = free_port()
    script = os.path.join(dir, 'user_agent_twisted.py')
    with open(script, 'w') as file:
        file.write(source.replace('3000', str(port)))

    # The output goes to a file, which the test reads while the example runs
    log = os.path.join(dir, 'output.log')
    with open(log, 'w') as output:
        process = subprocess.Popen([sys.executable, '-u', script], stdout=output, stderr=subprocess.STDOUT)
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            with open(log) as file:
                lines = file.read().splitlines()
            if lines.count('200 Hello from Twisted!') >= 2 or process.poll() is not None:
                break
            time.sleep(0.1)
    finally:
        process.send_signal(signal.SIGINT)
        try:
            process.wait(10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    with open(log) as file:
        lines = file.read().splitlines()
    ok(lines.count('200 Hello from Twisted!') >= 2, 'the timer requests the application of Twisted every second')
    is_ok(process.returncode, 0, 'stopped by INT')

# As the workflow Build runs it with the wheel: its server listens on a port that the system picks, so it needs no free
# port of the tests
with subtest('loopback_twisted.py'):
    result = subprocess.run(
        [sys.executable, os.path.join(EXAMPLES, 'loopback_twisted.py')], capture_output=True, text=True, timeout=60
    )
    is_ok(result.stdout, 'Pyjo_Reactor_Twisted\n200 Your Pyjo is working!\n', 'the response on the reactor of Twisted')
    is_ok(result.stderr, '', 'nothing on the standard error')
    is_ok(result.returncode, 0, 'the server and the user agent closed at the end')

done_testing()
