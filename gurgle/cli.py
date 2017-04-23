import os
import sys
import argparse
from colours import colour

from . import commands
from .server import Daemon
from .client import Client

from tornado.concurrent import Future
from tornado.ioloop import IOLoop
from tornado.gen import coroutine


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()

parser.add_argument(
    '-f',
    dest='gurglefile', metavar='FILE',
    type=os.path.abspath, default='gurglefile.py',
    help='Path to the gurglefile. Defaults to `./gurglefile.py`.')

parser.add_argument(
    '-p', '--port', default=7772,
    help='Port for the gurgle daemon to listen on. Defaults to 7772.')

parser.add_argument(
    '--pidfile', default=None,
    help='Path to the gurgle daemon pidfile. Defaults to `./.gurgle.pid`.')


def _sub_parser(name, func, help=''):
    sp = subparsers.add_parser(name, help=help)
    sp.set_defaults(func=func)
    return sp

def _command_parser(name, func, help=''):
    sp = _sub_parser(name, func, help)
    sp.add_argument('process', nargs='*')
    return sp

parser_start = _command_parser(
    'start', commands.start,
    'Start the named (or all) processes.')

parser_stop = _command_parser(
    'stop', commands.stop,
    'Stop the named (or all) processes.')
parser_stop.add_argument('--kill', action='store_true', default=False,
                         help='Kill the named processes.')

parser_listen = _command_parser(
    'listen', commands.listen,
    'Listen to the stdout/stderr streams of the named processes.')

parser_status = _sub_parser(
    'status', commands.status,
    'Get the status of all processes.')

parser_daemon = _sub_parser(
    'daemon', commands.daemon,
    'Start the gurgle dameon.')
parser_daemon.add_argument('--nofork', action='store_true', default=False)

parser_terminate = _sub_parser(
    'terminate',  commands.terminate,
    'Terminate the gurgle daemon and all running processes.')


def _finish(future):
    loop = IOLoop.current().stop()
    return future.result()


def cli():
    args = parser.parse_args()

    if not os.path.exists(args.gurglefile):
        print colour.red('Cannot find {}'.format(args.gurglefile))
        exit(1)

    pidfile = args.pidfile
    if not args.pidfile:
        pidfile = os.path.join(
            os.path.dirname(args.gurglefile),
            '.gurgle.pid')

    daemon = Daemon(pidfile)
    client = Client(args.port)

    resp = args.func(args, daemon, client)

    if isinstance(resp, Future):
        loop = IOLoop.current()
        loop.add_future(resp, _finish)
        loop.start()
