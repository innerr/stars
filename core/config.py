#coding:utf8
#
# Author: CMGS
# Created on 2011-3-15
#

import os
import sys

class Config(object):

    def __init__(self, configFile):
        self._config = {}
        if configFile == '':
            return
        configFile = isinstance(configFile, str) and [configFile] or configFile
        configFile = map(lambda path: os.path.abspath(path), configFile)
        self.load(configFile)

    def load(self, configFile):
        for config in configFile:
            prefix, config = os.path.split(config)
            sys.path.append(prefix)

            conf = __import__(config)
            if config.rfind('.') != -1:
                conf = sys.modules[config]

            for attr in dir(conf):
                if attr.startswith('__'):
                    continue
                self._config[attr] = getattr(conf, attr)

            sys.path.remove(prefix)
        return self._config

    def getConfig(self):
        return self._config

    def __getitem__(self, key):
        return self._config[key]

    def __getattr__(self, key):
        return self._config[key]

if __name__ == '__main__':
    c = Config('../../setting.py,../../setting2.py')
    print c.a
