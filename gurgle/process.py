import shlex
from functools import partial
from tornado.process import Subprocess

import logging
logger = logging.getLogger(__name__)


class ProcessMeta(type):
    PROCESSES = {}

    def __call__(cls, name, **kwargs):
        if name in ProcessMeta.PROCESSES:
            raise RuntimeError("Duplicate process '{}'".format(name))

        inst = type.__call__(cls, name, kwargs)
        ProcessMeta.PROCESSES[name] = inst
        return inst


class Process(object):
    __metaclass__ = ProcessMeta

    command = []

    def __init__(self, name, kwargs):
        self.name = name
        self.kwargs = kwargs

        self.proc = None
        self.exitcode = None

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

    def run(self):
        logger.info("Running %s", " ".join(self.command))
        self.proc = Subprocess(
            self._command,
            stdout=Subprocess.STREAM,
            stderr=Subprocess.STREAM)

        self._read(False, self.proc.stdout)
        self._read(True, self.proc.stderr)

    def _read(self, err, stream):
        stream.read_until('\n', partial(self._on_read, err, stream))

    def _on_read(self, err, stream, data):
        print "{} | {}".format(self.name, data)
        self._read(err, stream)

    def _exit(self, exitcode):
        self.proc = None
        self.exitcode = exitcode 
