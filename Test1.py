from MySSHLib import MySSHLib
import time
import logging

sh = MySSHLib(ip="192.168.145.128", username="testuser", password="test123",port=22)
sh.logger.setLevel(level=logging.ERROR)
sh.connect()
sh.sendAndWait("ifconfig\r", "$|#", breakCharacter="|", suppressCR=True)
print(sh.sessionLog)
sh.clearSessionLog()
sh.sendAndWait("uname -a\r", "$|#", breakCharacter="|", suppressCR=True)
sh.disconnect()
print(sh.sessionLog)
print("hi")
