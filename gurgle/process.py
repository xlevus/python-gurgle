import shlex
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


class Process(object):
    __metaclass__ = ProcessMeta

    command = []

    def __init__(self, name, **kwargs):
        self.name = name
        self.kwargs = kwargs

        self.proc = None
        self.exitcode = None
        self.subs = {}

    def __repr__(self):
        return "<Process({}): {}>".format(
            self.name,
            " ".join(self._command))

    @property
    def _vars(self):
        return dict(name=self.name, **self.kwargs)

    @property
    def _command(self):
        _vars = self._vars

        cmd = self.command[:]
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

        self.proc = Subprocess(
            self._command,
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
