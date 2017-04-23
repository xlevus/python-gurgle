from functools import partial
from tornado.process import Subprocess

import logging
logger = logging.getLogger(__name__)


class ProcessMeta(type):
    PROCESSES = {}

    def __new__(mcls, name, bases, attrs):
        if name in mcls.PROCESSES:
            raise RuntimeError('Duplicate process {}'.format(name))

        klass = super(ProcessMeta, mcls).__new__(mcls, name, bases, attrs)

        mcls.PROCESSES[name] = klass

        return klass


class Process(object):
    __metaclass__ = ProcessMeta

    command = []

    @property
    def name(self):
        return self.__class__.__name__

    def run(self):
        logger.info("Running %s", " ".join(self.command))
        proc = Subprocess(
            self.command,
            stdout=Subprocess.STREAM,
            stderr=Subprocess.STREAM)

        self._read(False, proc.stdout)
        self._read(True, proc.stderr)

        return proc

    def _read(self, err, stream):
        logger.info("Reading next line from %r", stream)
        stream.read_until('\n', partial(self._on_read, err, stream))

    def _on_read(self, err, stream, data):
        print "{} | {}".format(self.name, data)
        self._read(err, stream)
