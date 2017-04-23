import os
import imp
import json
from functools import wraps
import logging

import mattdaemon

import tornado.web
import tornado.websocket
import tornado.ioloop
from tornado import gen

from .process import ProcessMeta

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Error(Exception):
    http_status = 400


class UnknownProcess(Error):
    pass


class ProcessRunning(Error):
    pass


class ProcessNotRunning(Error):
    pass


def errorhandler(func):
    @wraps(func)
    @gen.coroutine
    def _inner(self, *args, **kwargs):
        try:
            resp = func(self, *args, **kwargs)
            if isinstance(resp, gen.Future):
                yield resp
        except Error as e:
            self.set_status(e.http_status)
            self.write({
                'error': True,
                'message': e.message,
                'type': e.__class__.__name__,
            })
            self.finish()
    return _inner


class ProcessMixin(object):
    @property
    def processes(self):
        return ProcessMeta.PROCESSES

    def get_process(self, name):
        try:
            return self.processes[name]
        except KeyError:
            raise UnknownProcess(name)


class Command(tornado.web.RequestHandler, ProcessMixin):

    @errorhandler
    @gen.coroutine
    def post(self, name):
        proc = self.get_process(name)
        resp = self.do_command(proc)
        if isinstance(resp, gen.Future):
            yield resp

    def do_command(self, process):
        raise NotImplementedError()


class RootHandler(Command):
    def get(self):
        self.write("OK\n")


class StatusHandler(tornado.web.RequestHandler, ProcessMixin):
    def get(self):
        output = {}

        for name, process in self.processes.iteritems():
            output[name] = {
                'running': process.running,
                'pid': process.pid,
                'command': process._command,
                'exitcode': process.exitcode,
            }

        self.write(output)


class RunHandler(Command):
    def do_command(self, process):
        if process.running:
            raise ProcessRunning(
                "Process '{0.name}' is already running".format(process))

        process.run()

        self.write({
            'error': False,
        })


class StopHandler(Command):
    @gen.coroutine
    def do_command(self, process):
        if not process.running:
            raise ProcessNotRunning(
                "Process '{0.name}' is not running".format(process))

        exitcode = yield process.stop(kill=self.get_argument('kill', default=False))
        self.write({
            'error': False,
            'exitcode': exitcode,
        })
        self.finish()


class StreamHandler(tornado.websocket.WebSocketHandler, ProcessMixin):
    def open(self):
        logger.info('Websocket opened')

    def on_message(self, message):
        logger.debug('WS Message: %r', message)
        try:
            msg = json.loads(message)
            proc = self.get_process(msg['subscribe'])
            proc.subscribe(self, self._sub)
        except ValueError as e:
            logger.debug("Error on message: %r", e)
            self.close()

    def on_close(self):
        for proc in self.processes.values():
            proc.unsubscribe(self)

    def _sub(self, process, stream, message):
        self.write_message({
            'process': process.name,
            'stream': stream,
            'message': message,
        })


def get_application(port):
    app = tornado.web.Application(
        [
            (r'/', RootHandler),
            (r'/api/status', StatusHandler),
            (r'/api/([A-Za-z0-9-]+)/start', RunHandler),
            (r'/api/([A-Za-z0-9-]+)/stop', StopHandler),
            (r'/stream.ws', StreamHandler),
        ],
        autoreload=False)
    app.listen(port)
    return app



class Daemon(mattdaemon.daemon):
    def run(self, *args, **kwargs):
        gurglefile = kwargs.pop('gurglefile')
        port = kwargs.pop('port')

        self._load_gurglefile(gurglefile)

        app = get_application(port)

        tornado.ioloop.IOLoop.current().start()

    def _load_gurglefile(self, gurglefile):
        wd = os.path.dirname(gurglefile)
        os.chdir(wd)
        logger.debug('Changed working directory to %r', os.getcwd())

        logger.debug('Loading %r', gurglefile)
        module = imp.load_source('gurglefile', gurglefile)
