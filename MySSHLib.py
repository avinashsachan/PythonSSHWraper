from paramiko import client, channel
import time
from datetime import datetime, timedelta
import logging
import threading


class MySSHLib:
    def __init__(self, ip: str, username: str, password: str, port: int = 22, timeout: int = 30):
        self.logger = logging.getLogger("MySSHLib")
        self.logger.setLevel(level=logging.ERROR)

        ch = logging.StreamHandler()
        ch.setLevel(level=logging.DEBUG)
        self.logger.addHandler(ch)

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
        self.timeout = timeout

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
            x = self.channel.recv(1024 * 10)
            if x != b'':
                z = x.decode("utf-8")
                self.logger.debug(z)
                self.sessionLog += z
                self.bufferLog = ((self.bufferLog + z)[-50:]).lower()
                t = threading.Thread(target=self.onReceiveData)
                t.start()
        except:
            pass

    def connect(self, connectTimeout=10, serverPrompt="$|#", separator="|", term="dumb"):
        try:
            term = term if term in ["vt100", "dumb"] else "dumb"
            self.client.connect(self.ip, port=self.port, username=self._username, password=self._password,
                                look_for_keys=False, timeout=connectTimeout)
            self.channel = self.client.invoke_shell(term=term, width=1600, height=1200)
            t = threading.Thread(target=self.onReceiveData)
            t.start()
            if serverPrompt is not None:
                self.wait(serverPrompt, separator)
        except Exception as e:
            raise e

    def wait(self, waitFor: str, breakCharacter: str = None):
        split_part = []
        try:
            if breakCharacter is None:
                split_part.append(waitFor.lower())
            else:
                split_part = [x.lower() for x in waitFor.split(breakCharacter)]
            dt = datetime.now() + timedelta(seconds=self.timeout)
            while datetime.now() <= dt:
                time.sleep(.05)
                for i in range(0, len(split_part)):
                    if split_part[i] in self.bufferLog:
                        return i

            raise TimeoutError("Exit not found")
        except:
            pass

    def sendMessage(self, command, suppressCR=False):
        if suppressCR:
            self.channel.send(command)
        else:
            self.channel.send(command + "\r")

    def sendAndWait(self, command, waitFor, breakCharacter, suppressCR=False):
        self.sendMessage(command, suppressCR)
        self.wait(waitFor, breakCharacter)

    def clearSessionLog(self):
        self.sessionLog = ""
        self.bufferLog = ""
