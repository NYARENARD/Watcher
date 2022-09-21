import discum
from threading import Thread
import time
from emoji import demojize
import socket
import re
from datetime import datetime
import pytz

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
        
        while True:
            try:
                self._sock.connect((self._server, self._port))
                break
            except Exception:
                time.sleep(5)

        self._sock.send(f"PASS {self._ttv_token}\n".encode('utf-8'))
        self._sock.send(f"NICK {self._nickname}\n".encode('utf-8'))
        for ch in self._ttv_channels:
            self._sock.send(f"JOIN {ch}\n".encode('utf-8'))
        self._logging("`>>> Подключение успешно.`")


    def __del__(self):
        self._sock.close()
        self.bot.gateway.close()
        self._logging("`>>> Соединение смотрящего сброшено.`")
	
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
                        self._logging(q[0])
                        q.pop(0)
                        time.sleep(1)
                except Exception:
                    pass

        def get_response():
            while True:
                while True:
                    try:
                        resp = demojize(self._sock.recv(2048).decode('utf-8'))
                        break
                    except Exception:
                        time.sleep(1)

                if resp.startswith('PING'):
                    self._sock.send("PONG\n".encode('utf-8'))

                elif len(resp) > 0:
                    try:
                        username, channel, message = re.search(':(.*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG #(.*) :(.*)', resp).groups()
                        tz_moscow = pytz.timezone('Europe/Moscow')
                        now = datetime.now(tz_moscow)
                        timestamp = "{}:{}:{} {}-{}-{}".format(now.hour, now.minute, now.second, now.day, now.month, now.year)
                        payload = "`{} | {} | {} | {}`".format(channel, timestamp, username.rjust(20), message)
                        q.append(payload)
                    except Exception:
                        pass

        q = []
        t1 = Thread(target=buff_queueing)
        t1.start()
        t2 = Thread(target=get_response)
        t2.start()

        @self.bot.gateway.command
        def into_file(resp):
            if resp.event.message:
                m = resp.parsed.auto()
                channelID = m["channel_id"]  
                messageID = m["id"]
                content = m["content"].lower()
                self_id = self.bot.gateway.session.user["id"]
                himself = (m["author"]["id"] == self_id)

                if channelID == self._log_channel and not himself:
                    content_arr = content.split(' ', 3)
                    command = content_arr[0]
                    filename = content_arr[1]
                    file_height = int(content_arr[2])
                    request = content_arr[3]

                    if command == "оформить":
                        self.bot.addReaction(channelID, messageID, '💬')
                        num_processed = 0
                        h_temp = file_height
                        with open(filename, 'w', encoding="utf-8") as f:
                            while num_processed < file_height:
                                if h_temp >= 25:
                                    diff = 25 
                                else:
                                    diff = h_temp
                                h_temp -= diff
                                try:
                                    searchResponse = self.bot.searchMessages(channelID=self._log_channel, textSearch=request, afterNumResults=num_processed, limit=diff)
                                    results = self.bot.filterSearchResults(searchResponse)
                                except KeyError:
                                    break
                                for message in results:
                                    to_input = message["content"]
                                    to_input = to_input.replace('`', '')
                                    to_input = to_input.replace('||', '')
                                    f.write(to_input + '\n')
                                num_processed += diff

                        self.bot.sendFile(self._log_channel, filename, isurl=False)
                        self.bot.addReaction(channelID, messageID, '✅')
                        import os
                        os.remove(filename)

        self.bot.gateway.run(auto_reconnect=True)
