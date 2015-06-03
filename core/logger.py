#coding:utf8
# Author: Pengweilin
# Date  : 2011.7.19

import os
import time

class ErrLogger:
    def __init__(self, filePath, logName):
        self._path = os.path.join(filePath, logName + '.log')
        self._path = os.path.realpath(self._path)
        if not os.path.exists(filePath):
            os.mkdir(filePath)

    def log(self, msg):
        now = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        fmtMsg = '[%s] %s\n' % (now, msg)
        f = open(self._path, 'a')
        f.write(fmtMsg)
        f.close()

    def error(self, msg):
        self.log(msg)

    def warning(self, msg):
        self.log(msg)

    def info(self, msg):
        self.log(msg)

