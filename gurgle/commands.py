import sys 
from functools import wraps

from tabulate import tabulate
from colours import colour

import tornado.ioloop
from tornado import gen

from .client import ClientError


def requires_gurgle(func):
    @wraps(func)
    def _inner(args, daemon, client):
        if not daemon.status():
            print colour.red("Gurgle is not running.")
            exit(1)
        return func(args, daemon, client)
    return _inner


def daemon(args, daemon, client):
    if not daemon.status():
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


@requires_gurgle
def terminate(args, daemon, client):
    print colour.blue("Terminating Gurgle...")
    daemon.stop()


@requires_gurgle
@gen.coroutine
def status(args, daemon, client):
    data = yield client.status()
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

        table.append([name, running, exitcode, pid])

    print tabulate(table,
                   ['name', 'status', 'exit', 'pid'])


@requires_gurgle
@gen.coroutine
def start(args, daemon, client):
    error = False

    for name in args.process:
        try:
            data = yield client.start(name)
        except ClientError as e:
            print "ERROR", colour.red(name), e.type
            error = True
        else:
            print "OK", colour.green(name)

    if error:
        exit(1)


@requires_gurgle
@gen.coroutine
def stop(args, daemon, client):
    error = False

    for name in args.process:
        try:
            data = yield client.stop(name, kill=args.kill)
        except ClientError as e:
            print colour.red("ERROR"), colour.bold_red(name), e.type
            error = True
        else:
            print colour.green("OK"), colour.bold_green(name)

    if error:
        exit(1)
