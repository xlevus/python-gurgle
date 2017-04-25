import sys
from itertools import cycle
from functools import wraps

from tabulate import tabulate
from colours import colour

import tornado.ioloop
from tornado import gen

from .client import ClientError


def daemon(args):
    if not args.daemon.status():
        print colour.blue("Starting Gurgle...")

        if args.nofork:
            daemon.should_daemonize = False
            daemon.stdout = sys.stdout
            daemon.stderr = sys.stderr

        daemon.start(
            gurglefile=args.gurglefile,
            port=args.port)
    else:
        print colour.red("Gurgle is already running.")


def terminate(args):
    print colour.blue("Terminating Gurgle...")
    args.daemon.stop()


@gen.coroutine
def status(args):
    data = yield args.client.status()
    table = []

    for name, details in sorted(data.items()):
        if details['running']:
            name = colour.bold_green(name)
        elif details['exitcode'] in (0, None):
            name = colour.yellow(name)
        else:
            name = colour.bold_red(name)

        running=(colour.green('RUNNING')
                 if details['running'] else colour.red('STOPPED'))

        exitcode = (details['exitcode'] or '')
        pid = (details['pid'] or '')

        command = ' '.join(details['command'])
        if len(command) > 80:
            command = command[:77] + '...'

        table.append(
            [name, running, exitcode, pid, command])

    print tabulate(table,
                   ['process', 'status', 'exit', 'pid', 'command'])


@gen.coroutine
def all_processes(client):
    data = yield client.status()
    raise gen.Return(data.keys())


@gen.coroutine
def start(args):
    error = False

    names = args.process
    if not names:
        names = yield all_processes(args.client)

    for name in names:
        try:
            data = yield args.client.start(name)
        except ClientError as e:
            print colour.red("ERROR"), colour.bold_red(name), e.type
            error = True
        else:
            print colour.green("OK"), colour.bold_green(name)

    if error:
        exit(1)


@gen.coroutine
def stop(args):
    error = False

    names = args.process
    if not names:
        names = yield all_processes(args.client)

    for name in names:
        try:
            data = yield args.client.stop(name, kill=args.kill)
        except ClientError as e:
            print colour.red("ERROR"), colour.bold_red(name), e.type
            error = True
        else:
            print colour.green("OK"), colour.bold_green(name)

    if error:
        exit(1)


@gen.coroutine
def listen(args):
    names = args.process
    if not names:
        names = yield all_processes(args.client)

    colour_map = dict(zip(
        names,
        cycle([colour.blue, colour.green, colour.cyan,
               colour.purple, colour.yellow, colour.light_grey,
               colour.dark_grey])))

    padding = max((len(x) for x in names))

    queue, fut = yield args.client.listen(names)
    loop = tornado.ioloop.IOLoop.current()
    loop.add_future(fut, lambda f: f)

    while fut.running():
        msg = yield queue.get()

        proc = msg['process']
        proc_c = colour_map[proc]

        if msg['stream'] == 'stderr':
            msg_c = colour.red
        else:
            msg_c = lambda x: x

        print proc_c(proc.rjust(padding)), '|', msg_c(msg['message'].rstrip())

