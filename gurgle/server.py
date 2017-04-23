import tornado.web


class RootHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("OK")


def get_application(port):
    app = tornado.web.Application([
        (r'/', RootHandler),
    ])
    app.listen(port)
    return app
