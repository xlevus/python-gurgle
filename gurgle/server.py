import imp

import mattdaemon

import tornado.web
import tornado.ioloop

from .process import ProcessMeta


class Command(tornado.web.RequestHandler):
    @property
    def processes(self):
        return ProcessMeta.PROCESSES


class RootHandler(Command):
    def get(self):
        self.write("OK\n")


class StatusHandler(Command):
    def get(self):
        output = {}

        for name, process in self.processes.iteritems():
            output[name] = {
                'running': process.running,
                'command': process._command,
                'exitcode': process.exitcode,
            }

        self.write(output)


def get_application(port):
    app = tornado.web.Application(
        [
            (r'/', RootHandler),
            (r'/api/status', StatusHandler),
        ],
        autoreload=False)
    app.listen(port)
    return app



class Daemon(mattdaemon.daemon):
    def run(self, *args, **kwargs):
        from time import sleep

        gurglefile = kwargs.pop('gurglefile')
        port = kwargs.pop('port')

        self._load_gurglefile(gurglefile)

        app = get_application(port)

        tornado.ioloop.IOLoop.current().start()

    def _load_gurglefile(self, gurglefile):
        module = imp.load_source('gurglefile', gurglefile)
