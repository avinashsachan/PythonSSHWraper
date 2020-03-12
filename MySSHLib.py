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
        self.channel = channel.Channel(chanid=100)
        self.sessionLog = ""
        self._bufferLog = ""
        self.timeout = timeout
        self._bufferSize = 1024 * 122

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
            x = self.channel.recv(self._bufferSize)
            if x is not None and x != b'':
                z = x.decode("utf-8")
                self.logger.debug(z)
                self.sessionLog += z
                self._bufferLog = ((self._bufferLog + z)[-50:]).lower()
                t = threading.Thread(target=self.onReceiveData)
                t.start()
        except:
            pass

    def connect(self, connectTimeout=10, serverPrompt="$|#", breakCharacter="|", term="vt100"):
        try:
            term = term if term in ["vt100", "dumb"] else "dumb"
            self.client.load_system_host_keys()
            self.client.set_missing_host_key_policy(client.AutoAddPolicy())
            self.client.connect(self.ip, port=self.port, username=self._username, password=self._password,
                                look_for_keys=False, timeout=connectTimeout)
            self.logger.debug("connected")
            self.channel = self.client.invoke_shell(term=term, width=1600, height=1200)
            t = threading.Thread(target=self.onReceiveData)
            t.start()
            if serverPrompt is not None:
                self.wait(serverPrompt, breakCharacter)

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
                    if split_part[i] in self._bufferLog:
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
        self._bufferLog = ""
        self.sendMessage(command, suppressCR)
        return self.wait(waitFor, breakCharacter)

    def clearSessionLog(self):
        self.sessionLog = ""
        self._bufferLog = ""

    # def sendCommand(self, command):
    #     # Check if connection is made previously
    #     print("1")
    #     if self.client:
    #         stdin, stdout, stderr = self.client.exec_command(command)
    #         while not stdout.channel.exit_status_ready():
    #             # Print stdout data when available
    #             if stdout.channel.recv_ready():
    #                 # Retrieve the first 1024 bytes
    #                 alldata = stdout.channel.recv(1024)
    #                 while stdout.channel.recv_ready():
    #                     # Retrieve the next 1024 bytes
    #                     alldata += stdout.channel.recv(1024)
    #
    #                 # Print as string with utf8 encoding
    #                 print(12,str(alldata, "utf8"))
    #     else:
    #         print("Connection not opened.")