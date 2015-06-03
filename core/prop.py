#coding:utf-8
#nature@20100825

import os

class Props:
    def __init__(self, file=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'props.data')):
        self._file = file
        self._data = {}
        self._load()

    def _load(self):
        if not os.path.isfile(self._file):
            open(self._file, 'wb').close()
        file = open(self._file, 'rb')
        for it in file.readlines():
            kv = it.split('=')
            if len(kv) == 2:
                self._data[kv[0]] = kv[1][:-1]
        file.close()

    def set(self, key, value):
        self._data[str(key)] = str(value)

    def get(self, key):
        return self._data.get(str(key))

    def save(self):
        file = open(self._file, 'wb')
        for k, v in self._data.items():
            file.write(k + '=' + v + '\n')
        file.close()
