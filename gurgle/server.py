import os
import imp
import logging 

import mattdaemon

import tornado.web
import tornado.ioloop

from .process import ProcessMeta

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


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

class RunHandler(Command):
    def post(self, process):
        try:
            proc = self.processes[process]
            proc.run()
            self.write({
                'error': False,
            })
        except KeyError:
            self.set_status(400)
            self.write({
                'error': 'Unknown process',
            })


def get_application(port):
    app = tornado.web.Application(
        [
            (r'/', RootHandler),
            (r'/api/status', StatusHandler),
            (r'/api/([A-Za-z0-9-]+)/run', RunHandler),
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
