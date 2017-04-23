import argparse

import tornado.log
import tornado.ioloop
import tornado.iostream


from .process import Process

class Ying(Process):
    command = ['./test/repeat', 'ying', '1']


class Yang(Process):
    command = ['./test/repeat', 'ying', '1']


def cli():
    y = Ying()
    y2 = Yang()
ioloop = tornado.ioloop.IOLoop.current()

    from .server import get_application
    app = get_application(8888)

    ioloop.add_callback(y.run)

    ioloop.start()


cli()
