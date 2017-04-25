import os
import sys
import argparse
import traceback
from colours import colour

from . import commands
from . import server
from . import client
from .util import load_gurglefile

from tornado.concurrent import Future
from tornado.ioloop import IOLoop
from tornado.gen import coroutine


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()


def _host_port(arg):
    host, port = arg.split(':')

    host = host or None
    port = int(port or 7774)

    return host, port


parser.add_argument(
    '-f',
    dest='gurglefile', metavar='FILE',
    type=os.path.abspath, default='gurglefile.py',
    help='Path to the gurglefile. Defaults to `./gurglefile.py`')

parser.add_argument(
    '-l', '--listen', nargs='?', metavar='HOST:PORT',
    type=_host_port, default=('127.0.0.1', 7772),
    help=':port or host:port to expose (or connect) via a hostname.')

parser.add_argument(
    '--nofork',
    dest='fork',
    action='store_false', default=True,
    help='Do not fork to the background.')


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

parser_terminate = _sub_parser(
    'terminate',  commands.terminate,
    'Terminate the gurgle daemon and all running processes.')


def _finish(future):
    loop = IOLoop.current().stop()
    return future.result()


def _find_gfile(args):
    g_file = args.gurglefile

    if os.path.isdir(g_file):
        g_file = os.path.join(g_file, 'gurglefile.py')

    if not os.path.exists(g_file):
        print colour.red('Cannot find {}'.format(g_file))
        exit(1)

    try:
        load_gurglefile(g_file)
    except:
        print colour.red("There was an error loading '{}'".format(
            g_file))
        traceback.print_exc()
        exit(1)

    root = os.path.dirname(g_file)

    return root, g_file


def cli():
    args = parser.parse_args()

    root, g_file = _find_gfile(args)

    args.client = client.Client(*args.listen)
    args.daemon = server.get_daemon(root, args.listen, args.fork)

    if not args.daemon.status():
        args.daemon.start()

    resp = args.func(args)

    if isinstance(resp, Future):
        loop = IOLoop.current()
        loop.add_future(resp, _finish)
        loop.start()
