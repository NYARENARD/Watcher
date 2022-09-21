import discum
from threading import Thread
import time

from emoji import demojize
import socket
import re

class Watcher(Thread):
    
    def __init__(self, cfg):
        Thread.__init__(self)
        self._token = cfg["token"]
        self._prefix = cfg["prefix"]
        self._log_channel = cfg["logchannel"]
        self._ttv_channels = cfg["ttv_channels"].split()
        self._nickname = cfg["nickname"]
        self._ttv_token = cfg["ttv_token"]
        self.bot = discum.Client(token = self._token, log=False)

        self._sock = socket.socket()
        self._server = 'irc.chat.twitch.tv'
        self._port = 6667

        try:
            self._sock.connect((self._server, self._port))
        except Exception:
            self._sock.connect((self._server, self._port))

        self._sock.send(f"PASS {self._ttv_token}\n".encode('utf-8'))
        self._sock.send(f"NICK {self._nickname}\n".encode('utf-8'))
        for ch in self._ttv_channels:
            self._sock.send(f"JOIN {ch}\n".encode('utf-8'))


    def __del__(self):
        self._sock.close()
        self.bot.gateway.close()
        self._logging("msg", "`>>> Соединение смотрящего сброшено.`")
	
    def run(self):
        self._watcher_launch()

    def _logging(self, message, attachments = []):
        print(message)
        self.bot.sendMessage(self._log_channel, message)
        for url in attachments:
            self.bot.sendFile(self._log_channel, url, isurl=True)

    def _watcher_launch(self):
        def buff_queueing():
            while True:
                try:
                    if q[0]:
                        self.bot.sendMessage(self._log_channel, q[0])
                        q.pop(0)
                        time.sleep(1)
                except Exception:
                    pass

        def get_response():
            while True:
                resp = demojize(self._sock.recv(2048).decode('utf-8'))

                if resp.startswith('PING'):
                    self._sock.send("PONG\n".encode('utf-8'))

                elif len(resp) > 0:
                    try:
                        username, channel, message = re.search(':(.*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG #(.*) :(.*)', resp).groups()
                        payload = "`{} | {} | {}`".format(channel, username.rjust(20), message)
                        q.append(payload)
                    except Exception:
                        pass

        q = []
        t1 = Thread(target=buff_queueing)
        t1.start()
        t2 = Thread(target=get_response)
        t2.start()

        

        self.bot.gateway.run(auto_reconnect=True)
