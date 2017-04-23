import os
import sys
import argparse

from . import commands
from .server import Daemon

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()

parser.add_argument('-f', '--gurglefile',
                    type=os.path.abspath,
                    default='gurglefile')
parser.add_argument('-p', '--port', default=7772)
parser.add_argument('--pidfile',
                    type=os.path.abspath,
                    default=None)
parser.add_argument('--nofork', action='store_true', default=False)


def _sub_parser(name, func):
    sp = subparsers.add_parser(name)
    sp.set_defaults(func=func)
    return sp

def _command_parser(name, func):
    sp = _sub_parser(name, func)
    sp.add_argument('command', nargs='*')
    return sp

parser_run = _command_parser('run', None)

parser_status = _sub_parser('status', commands.status)

parser_start = _sub_parser('start', commands.start)
parser_terminate = _sub_parser('terminate',  commands.terminate)


def cli():
    args = parser.parse_args()

    pidfile = args.pidfile
    if not args.pidfile:
        pidfile = os.path.join(
            os.path.dirname(args.gurglefile),
            '.gurgle.pid')

    if args.nofork:
        kwargs = {
            'daemonize': False,
            'stdout': sys.stdout,
            'stderr': sys.stderr,
        }
    else:
        kwargs = {
            'daemonize': True,
        }
    daemon = Daemon(pidfile, **kwargs)

    args.func(args, daemon)
