import json
from functools import partial

from tornado import gen
from tornado import httpclient
from tornado import websocket
from tornado import queues


class ClientError(Exception):
    def __init__(self, type, message):
        self.type = type
        self.message = message

    def __repr__(self):
        return '{}({})'.format(self.type, self.message)


class Client(object):
    def __init__(self, host, port):
        self.port = port
        self.client = httpclient.AsyncHTTPClient()

    def _url(self, path):
        return 'http://localhost:{}{}'.format(self.port, path)

    @gen.coroutine
    def _request(self, method, path, **kwargs):
        req = httpclient.HTTPRequest(
            url=self._url(path),
            body='' if method == 'POST' else None,
            method=method)

        try:
            resp = yield self.client.fetch(req)
            data = json.loads(resp.body)
        except httpclient.HTTPError as e:
            if e.code == 500:
                raise

            resp = e.response
            try:
                data = json.loads(resp.body)
                raise ClientError(type=data['type'],
                                  message=data['message'])
            except ValueError:
                raise e

        raise gen.Return(data)

    def _command(self, command, process, **kwargs):
        path = '/api/{}/{}'.format(process, command, **kwargs)
        return self._request('POST', path)

    def start(self, process):
        return self._command('start', process)

    def stop(self, process, kill=False):
        return self._command('stop', process, kill=kill)

    def status(self):
        return self._request('GET', '/api/status')

    @gen.coroutine
    def _listen(self, queue, conn):
        while True:
            msg = yield conn.read_message()
            if msg is None:
                break

            data = json.loads(msg)
            yield queue.put(data)

    @gen.coroutine
    def listen(self, processes):
        conn = yield websocket.websocket_connect(
            'ws://localhost:{}/stream.ws'.format(self.port))

        for p in processes:
            print "Subscribing to", p
            conn.write_message(json.dumps({
                'subscribe': p
            }))

        queue = queues.Queue()
        raise gen.Return((queue, self._listen(queue, conn)))
