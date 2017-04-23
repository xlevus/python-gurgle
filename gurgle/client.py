import json
from functools import partial

from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest


class ClientError(Exception):
    def __init__(self, type, message):
        self.type = type
        self.message = message

    def __repr__(self):
        return '{}({})'.format(self.type, self.message)


class Client(object):
    def __init__(self, port):
        self.port = port
        self.client = AsyncHTTPClient()

    @gen.coroutine
    def _request(self, method, path, **kwargs):
        req = HTTPRequest(
            url='http://localhost:{}{}'.format(self.port, path),
            method=method)

        resp = yield self.client.fetch(req)

        data = json.loads(resp.body)

        if data.get('error'):
            raise ClientError(
                type=data['type'],
                message=data['message'])

        raise gen.Return(data)

    def _command(self, command, process, **kwargs):
        path = '/api/{}/{}'.format(command, process, **kwargs)
        return self._request('POST', path)

    def status(self):
        return self._request('GET', '/api/status')
