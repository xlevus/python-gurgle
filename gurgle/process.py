import os
import shlex
import contextlib
from functools import partial

from tornado import gen
from tornado.process import Subprocess
from tornado import ioloop
from tornado import iostream

import logging
logger = logging.getLogger(__name__)


class ProcessMeta(type):
    PROCESSES = {}

    def __call__(cls, name, *args, **kwargs):
        if name in ProcessMeta.PROCESSES:
            raise RuntimeError("Duplicate process '{}'".format(name))

        inst = type.__call__(cls, name, *args, **kwargs)
        ProcessMeta.PROCESSES[name] = inst
        return inst


class CommandMixin(object):
    def command_prefix(self):
        return []

    def command_suffix(self):
        return []

    def __enter__(self):
        pass

    def __exit__(self, *_):
        pass


class Argument(CommandMixin):
    def __init__(self, *args):
        self.args = args

    def __repr__(self):
        return "<Args: {}>".format(" ".join(self.args))

    def command_suffix(self):
        return list(self.args)


class Environ(CommandMixin):
    def __init__(self, *args, **kwargs):
        self.environ = dict(args, **kwargs)

    def __repr__(self):
        return "<Environ: {}>".format(" ".join(self.environ,keys()))

    def __enter__(self):
        self._original_state = {}
        for key in self.environ:
            if key in os.environ:
                self._original_state[key] = os.environ[key]
            os.environ[key] = self.environ[key]

    def __exit__(self, *_):
        for key in self.environ:
            if key in self._original_state:
                os.environ[key] = self._original_state
            else:
                del os.environ[key]
        del self._original_state


class Wrapper(CommandMixin):
    def __init__(self, *args):
        self.prefix = args

    def command_prefix(self):
        return list(self.prefix)


class Process(object):
    __metaclass__ = ProcessMeta

    command = []

    def __init__(self, name, *mixins, **kwargs):
        self.name = name
        self.kwargs = kwargs
        self.mixins = mixins

        self.proc = None
        self.exitcode = None
        self.subs = {}

    def __repr__(self):
        return "<Process({}): {}>".format(
            self.name,
            " ".join(self.format_command()))

    def __str__(self):
        return self.name

    def command_vars(self):
        return dict(name=self.name, **self.kwargs)

    def format_command(self):
        _vars = self.command_vars()

        cmd = self.command[:]

        for mixin in self.mixins:
            cmd = mixin.command_prefix() + cmd + mixin.command_suffix()

        if isinstance(cmd, (str, unicode)):
            cmd = shlex.split(cmd)

        for i, part in enumerate(cmd):
            cmd[i] = part.format(**_vars)

        return cmd

    @property
    def running(self):
        return self.proc is not None

    @property
    def pid(self):
        return self.proc.pid if self.proc else None

    def run(self):
        logger.info("Running %s", " ".join(self.command))

        with contextlib.nested(*self.mixins):
            self.proc = Subprocess(
                self.format_command(),
                stdout=Subprocess.STREAM,
                stderr=Subprocess.STREAM)

        self._exit_future = self._wait_for_exit()
        self._start_read('stdout', self.proc.stdout)
        self._start_read('stderr', self.proc.stderr)

    @gen.coroutine
    def stop(self, kill=False):
        proc = self.proc.proc
        if kill:
            logger.info("Killing %r [PID %i]", self, self.pid)
            proc.kill()
        else:
            logger.info("Terminating %r [PID %i]", self, self.pid)
            proc.terminate()

        exitcode = yield self._exit_future
        raise gen.Return(exitcode)

    def subscribe(self, id, cb):
        logger.info("Subscription: %r added", id)
        self.subs[id] = cb

    def unsubscribe(self, id):
        try:
            del self.subs[id]
            logger.info("Subscription: %r removed", id)
        except KeyError:
            pass

    @gen.coroutine
    def _wait_for_exit(self):
        exitcode = yield self.proc.wait_for_exit(False)
        logger.info("Process %r stopped", self)
        self.proc = None
        self.exitcode = exitcode
        self.subs = {}
        raise gen.Return(exitcode)

    def _start_read(self, label, stream):
        loop = ioloop.IOLoop.current()
        loop.add_future(self._read(label, stream), lambda f: f)

    @gen.coroutine
    def _read(self, label, stream):
        try:
            while self.running:
                msg = yield stream.read_until('\n')
                for sub_cb in self.subs.itervalues():
                    sub_cb(self, label, msg)
        except iostream.StreamClosedError:
            pass
