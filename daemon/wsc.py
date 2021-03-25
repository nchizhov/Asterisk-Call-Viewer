#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tornado import websocket, web, ioloop
from json import dumps, loads
import threading
from uuid import uuid4


class SocketHandler(websocket.WebSocketHandler):
    def data_received(self, chunk):
        pass

    clients = {}

    def __init__(self, *argv, **kwargs):
        self.func = kwargs.pop('func')
        super(SocketHandler, self).__init__(*argv, **kwargs)

    def open(self):
        self.id = str(uuid4())
        if self.id not in self.clients:
            self.clients[self.id] = self
        sdata = {'action': 'setid',
                 'id': self.id}
        self.write_message(dumps(sdata))

    def on_message(self, message):
        self.func(loads(message))

    def on_close(self):
        if self.id in self.clients:
            del self.clients[self.id]

    def check_origin(self, origin):
        return True


class WSocketServer(threading.Thread):
    def __init__(self, func, port=8888):
        self.app = web.Application([
            (r'/', SocketHandler, {'func': func}),
        ])
        self.port = port
        threading.Thread.__init__(self)

    def run(self):
        self.app.listen(self.port)
        ioloop.IOLoop.instance().start()

    def send(self, data, client=''):
        data = dumps(data)
        if client:
            if client in SocketHandler.clients:
                SocketHandler.clients[client].write_message(data)
        else:
            for client in SocketHandler.clients.values():
                client.write_message(data)
