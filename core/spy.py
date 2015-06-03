#coding:utf-8
#nature@20100316

import time
import threading
import copy
import traceback

class Spy:
    def __init__(self, max = 120):
        self._freqs = []
        self._records = []
        self._max = max
        self._flock = threading.Lock()
        self._rlock = threading.Lock()

    def increase(self, key):
        '{key: times}'
        self._flock.acquire()
        try:
            data = self._get(self._freqs)
            value = data.get(key)
            if value:
                data[key] = value + 1
            else:
                data[key] = 1
        except:
            traceback.print_exc()
        self._flock.release()

    def record(self, key, value):
        '{key: [values]} -> {key: [min, max, sum, count]}'
        value = int(value)
        self._rlock.acquire()
        try:
            data = self._get(self._records)
            record = data.get(key)
            if record:
                record['min'] = min(value, record['min'])
                record['max'] = max(value, record['max'])
                record['sum'] = value + record['sum']
                record['count'] = 1 + record['count']
            else:
                record = {}
                data[key] = record
                record['min'] = value
                record['max'] = value
                record['sum'] = value
                record['count'] = 1
        except:
            traceback.print_exc()
        self._rlock.release()

    def getMax(self):
        return self._max

    def setMax(self, max):
        self._max = int(max)

    def getFreqs(self):
        self._flock.acquire()
        try:
            clone = copy.deepcopy(copy.deepcopy(self._freqs))
        except:
            traceback.print_exc()
        self._flock.release()
        return clone

    def getRecords(self):
        self._rlock.acquire()
        try:
            clone = copy.deepcopy(copy.deepcopy(self._records))
        except:
            traceback.print_exc()
        self._rlock.release()
        return clone

    def detach(self):
        self._flock.acquire()
        try:
            freqs = self._freqs
            self._freqs = []
        except:
            traceback.print_exc()
        self._flock.release()
        self._rlock.acquire()
        try:
            records = self._records
            self._records = []
        except:
            traceback.print_exc()
        self._rlock.release()
        return freqs, records

    def getGreaterFreqs(self, timestamp):
        self._flock.acquire()
        try:
            clone = self._getGreater(self._freqs, timestamp)
        except:
            traceback.print_exc()
        self._flock.release()
        return clone

    def getGreaterRecords(self, timestamp):
        self._rlock.acquire()
        try:
            clone = self._getGreater(self._records, timestamp)
        except:
            traceback.print_exc()
        self._rlock.release()
        return clone

    def _get(self, datas):
        timestamp = int(time.time() / 60) * 60
        for it in datas:
            if it[0] == timestamp:
                return it[1]
        data = {}
        datas.insert(0, (timestamp, data))
        if len(datas) > self._max:
            datas.pop()
        return data

    def _getGreater(self, datas, timestamp):
        timestamp = int(timestamp)
        index = -1
        for i in range(0, len(datas)):
            if timestamp > datas[i][0]:
                return datas[0:i]
        return datas
