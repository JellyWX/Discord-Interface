base_uri = 'https://discordapp.com/api'
token = 'MzU1MTAxMzU1NDgyMDIxODg5.DaapFg.d0Ygl-vmyc4Z2z0ChdYSz-b1jsg'
auth = 'Bot ' + token

from tornado import escape
from tornado import gen
from tornado import httpclient
from tornado import httputil
from tornado import ioloop
from tornado import websocket

import functools
import json
import time
import requests
import asyncio


class WebSocketClient():
    def connect(self):
        res = requests.get(base_uri + '/gateway/bot', headers={'Authorization': auth})
        gateway = res.json()['url']

        ws_conn = websocket.websocket_connect(gateway)
        ws_conn.add_done_callback(self._connect_callback)

    def send(self, data):
        if not self._ws_connection:
            raise RuntimeError('Web socket connection is closed.')

        self._ws_connection.write_message(escape.utf8(json.dumps(data)))

    def close(self):
        if not self._ws_connection:
            raise RuntimeError('Web socket connection is already closed.')

        self._ws_connection.close()

    def _connect_callback(self, future):
        if future.exception() is None:
            self._ws_connection = future.result()
            self._on_connection_success()
            self._read_messages()
        else:
            self._on_connection_error(future.exception())

    @gen.coroutine
    def _read_messages(self):
        while True:
            msg = yield self._ws_connection.read_message()
            if msg is None:
                self._on_connection_close()
                break

            self._on_message(msg)

    def _on_message(self, msg):
        """This is called when new message is available from the server.
        :param str msg: server message.
        """

        pass

    def _on_connection_success(self):
        """This is called on successful connection ot the server.
        """

        pass

    def _on_connection_close(self):
        """This is called when server closed the connection.
        """
        pass

    def _on_connection_error(self, exception):
        """This is called in case if connection to the server could
        not established.
        """

        pass


class DiscordWS(WebSocketClient):
    heartbeat = None
    sequence_number = 0
    connection_status = 0

    def _on_message(self, msg):
        data = json.loads(msg)
        print(data)

        if data['op'] == 10:
            self.connection_status = 1
            self.heartbeat = data['d']['heartbeat_interval']
            self.send({
                'op': 2,
                'd': {
                    "token": token,
                    "properties": {
                        "$os": "linux",
                        "$browser": "discord-interface",
                        "$device": "discord-interface"
                    },
                    "compress": False,
                    "large_threshold": 150,
                    "presence": {
                        "game": {
                            "name": "Cards Against Humanity",
                            "type": 0
                        },
                        "status": "online",
                        "since": 91879201,
                        "afk": False
                    }
                },
            })


    def _on_connection_success(self):
        print('Connected')

    def _on_connection_close(self):
        print('Connection closed')
        self.connection_status = 2

    def _on_connection_error(self, exception):
        print('Connection error: %s', exception)


    async def send_heartbeat(self):
        while self.connection_status == 0:
            await asyncio.sleep(2.5)

        while self.connection_status != 2:
            if self.connection_status == 1:
                print('Heartbeating')
                self.send({
                    'op': 1,
                    'd': None,
                    })

                await asyncio.sleep(self.heartbeat / 1000)


def main():
    client = DiscordWS()
    client.connect()

    try:
        loop = asyncio.get_event_loop()
        loop.create_task(client.send_heartbeat())
        loop.run_forever()
    except KeyboardInterrupt:
        client.close()


if __name__ == '__main__':
    main()
