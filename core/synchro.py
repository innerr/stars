#coding:utf-8
#nature@20100825

import time
import threading
import thread
import bisect
import copy
import traceback

class ISyncer:
    'Interface of syncer using in ClientSync/ClusterSync. Datas should NOT be cached because the instance may be shared by ClientSync(s).'
    def fetch(self, cls):
        'Return datas by calling cls, or whatever you want. This function is NOT thread safe.'
        pass

    def merge(self, origin, data):
        'Merge two fetched datas and return the merged result. This function is thread safe.'
        pass

class SyncTasks:
    def __init__(self, taskPrefix='synchro.'):
        self._threads = {}
        self.taskPrefix = taskPrefix
        self.__getitem__ = self._threads.__getitem__
        self.items = self._threads.items

    def thread(self, threadName):
        threadName = self.taskPrefix + threadName
        if not self._threads.has_key(threadName):
            self._threads[threadName] = []
        threads = self._threads
        class Thread:
            def add(self, dataName, syncer):
                threads[threadName].append((dataName, syncer))
        return Thread()

    def add(self, name, syncer):
        self.thread(name).add(name, syncer)

class ClusterSync:
    def __init__(self, cluster, runner, taskPrefix='synchro.'):
        self._runner = runner
        self._cluster = cluster
        self._tasks = SyncTasks()
        self.add = self._tasks.add
        self.thread = self._tasks.thread

        self._syncs = {}
        for client in cluster:
            self._syncs[client.url] = ClientSync(client, self._runner, self._tasks)
        self.start = lambda interval: map(lambda x: x.start(interval), self._syncs.values())
        self.dump = lambda: map(lambda x: x.dump(), self._syncs.values())
        self.stop = lambda: map(lambda x: x.stop(), self._syncs.values())

    def load(self, url):
        self._cluster.load(url)
        self._syncs[url] = ClientSync(self._cluster[url], self._runner, self._tasks)

    def remove(self, url):
        self._cluster.remove(url)
        sync = self._syncs.get(url)
        if sync:
            self._syncs.pop(url)
            sync.stop()

class ClientSync:
    def __init__(self, cls, runner, tasks=SyncTasks()):
        self.url = cls.url
        self.add = tasks.add
        self.thread = tasks.thread
        self._tasks = tasks
        self._datas = {}
        self._cls = cls
        self._syncing = StatusData(self._cls.url)
        self._runner = runner
        self._interval = -1

    def dump(self):
        trim = lambda x: x.startswith(self._tasks.taskPrefix) and x[len(self._tasks.taskPrefix):] or x
        results = {'syncing': self._syncing.dump()}
        for thread, syncers in self._tasks.items():
            data = self._datas[thread]
            if len(syncers) == 1:
                name, syncer = syncers[0]
                lock, result = data[0]
                name = trim(name)
                lock.acquire()
                try:
                    results[name] = copy.deepcopy(result)
                except:
                    traceback.print_exc()
                lock.release()
            else:
                values = {}
                for i in range(0, len(syncers)):
                    name, syncer = syncers[i]
                    lock, result = data[i] 
                    lock.acquire()
                    try:
                        values[name] = copy.deepcopy(result)
                    except:
                        traceback.print_exc()
                    lock.release()
                thread = trim(thread)
                results[thread] = values
        return results

    def start(self, interval):
        if self._interval >= 0:
            return
        self._interval = interval
        for name, syncers in self._tasks.items():
            data = self._datas.get(name)
            if not data:
                data = []
                self._datas[name] = data
            while len(data) < len(syncers):
                data.append((threading.Lock(), None))
            self._runner.run(name, self._work, interval, {'cls': self._cls, 'syncers': syncers, 'syncing': self._syncing, 'data': data})

    def stop(self):
        for name, syncers in self._tasks.items():
            self._runner.stop(name)
        self._interval = -1

    @staticmethod
    def _work(cls, syncers, syncing, data):
        try:
            for i in range(0, len(syncers)):
                name, syncer = syncers[i]
                lock, result = data[i]
                fetched = syncer.fetch(cls)
                lock.acquire()
                try:
                    data[i] = (lock, syncer.merge(result, fetched))
                except:
                    traceback.print_exc()
                lock.release()
        except Exception, e:
            if type(e).__name__ == 'RpcFailed':
                syncing.failed()
            else:
                syncing.exception()
                traceback.print_exc()
            return
        syncing.succeeded()

class SpySyncer:
    def __init__(self, max, function):
        self._function = function
        self._max = max
        self._timeOffset = max + 1

    def fetch(self, cls):
        timestamp = int(time.time() - self._timeOffset * 60)
        datas = getattr(cls, self._function)(timestamp)
        assert isinstance(datas, list) and len(datas) == 2 and datas[0] == 'ok', datas
        fetched = len(datas)
        if fetched > 2:
            self._timeOffset = max(2, int(self._timeOffset / 2))
        elif fetched < 2:
            self._timeOffset = min(self._max + 1, self._timeOffset * 2)
        return datas[1]

    def merge(self, origin, datas):
        return self._combine(origin, datas)[-self._max:]

    @staticmethod
    def _combine(origin, datas):
        if not datas:
            return origin or []
        datas.reverse()
        if not origin:
            return datas or []
        index = bisect.bisect_left(map(lambda x: x[0], origin), datas[0][0])
        return origin[:index] + datas

class ValueSyncer:
    def __init__(self, function):
        self._function = function
        self.merge = lambda origin, data: data

    def fetch(self, cls):
        result = getattr(cls, self._function)()
        if isinstance(result, list) and len(result) > 1 and result[0] == 'ok':
            if len(result) == 2:
                return result[1]
            else:
                return result[1:]
        return result

class ResultData:
    def __init__(self, syncers):
        pass

class StatusData:
    def __init__(self, url):
        self.url = url
        self._lock = threading.Lock()
        self._offlineTime = -1
        self._timeoutCount = 0
        self._status = 'unknown'

    def failed(self):
        self._lock.acquire()
        if self._status != 'ok':
            self._timeoutCount += 1
        else:
            self._offlineTime = int(time.time())
        self._status = 'offline'
        self._lock.release()

    def exception(self):
        self._lock.acquire()
        self._status = 'exception'
        self._lock.release()

    def succeeded(self):
        self._lock.acquire()
        self._timeoutCount = 0
        self._offlineTime = -1
        self._status = 'ok'
        self._lock.release()

    def dump(self):
        return {'url': self.url, 'status': self._status, 'offlineTime': self._offlineTime, 'timeoutCount': self._timeoutCount}
    
class LazyFetcher:
    def __init__(self, cluster, function):
        self._function = function
        self._cluster = cluster
        self._values = []
        for i in range(0, len(cluster)):
            self._values.append(None)
        self.__len__ = self._values.__len__

    def __getitem__(self, i):
        value = self._values[i]
        if value == None:
            result = getattr(self._cluster[i], self._function)()
            if isinstance(result, list) and len(result) == 2 and result[0] == 'ok':
                value = result[1]
                self._values[i] = value
        return value

if __name__ == '__main__':
    import os
    import init
    import daemons
    import cluster
    import client

    key = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + '/_keys/private/leo.pem'
    tasks = daemons.Daemons()
    cls = cluster.Cluster(key)
    cls._load('127.0.0.1/storage/0')
    cls._load('127.0.0.1/storage/1')
    cls._load('127.0.0.1/storage/2')
    cls._load('127.0.0.1/storage/3')

    sync = ClusterSync(cls, tasks)
    sync.add('records', SpySyncer(10, 'spyGetRecords'))
    sync.add('freqs', SpySyncer(10, 'spyGetFreqs'))
    sync.thread('values').add('auth.size', ValueSyncer('authGetSize'))
    sync.thread('values').add('spy.max', ValueSyncer('spyGetMax'))
    sync.thread('values').add('storage.size', ValueSyncer('size'))
    sync.start(1)

    for i in xrange(0, 30):
        for data in sync.dump():
            print data['syncing'], data.get('values')
            print data['records'] and map(lambda x: x[0], data['records']) or []
            print data['freqs'] and map(lambda x: x[0], data['freqs']) or []
        print
        time.sleep(1)
    tasks.terminate(10)
    print 'Running(Should be [])', tasks.running()
    print 'Done'
