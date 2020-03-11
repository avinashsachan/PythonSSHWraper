from paramiko import client, channel
import time
from datetime import datetime, timedelta
import logging
import threading


class MySSHLib:
    def __init__(self, ip, port, username, password):
        self.ip = ip
        self.port = port
        self._username = username
        self._password = password
        self.client = client.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(client.AutoAddPolicy())
        self.channel = channel.Channel(chanid=100)
        self.sessionLog = ""
        self.bufferLog = ""

    def __del__(self):
        self.disconnect()

    def disconnect(self):
        try:
            self.channel.close()
            self.client.close()
        except:
            pass

    def onReceiveData(self):
        try:
            if self.client is None or self.channel is None: return
            x = self.channel.recv(1024)
            if x != b'':
                z = x.decode("utf-8")
                self.sessionLog += z
                self.bufferLog = (self.bufferLog + z)[-50:]
                t = threading.Thread(target=self.onReceiveData)
                t.start()
        except:
            pass

    def connect(self, connectTimeout=10, serverPrompt="$|#", separator="|", term="dumb"):
        try:
            term = term if term in ["vt100", "dumb"] else "dumb"
            self.client.connect(self.ip, port=self.port, username=self.username, password=self.password,
                                look_for_keys=False, timeout=connectTimeout)
            self.channel = self.client.invoke_shell(term=term, width=1600, height=1200)
            t = threading.Thread(target=self.onReceiveData)
            t.start()
        except Exception as e:
            raise e
