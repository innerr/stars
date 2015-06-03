#coding:utf-8
    
import threading
import synchro
import spystat

class SequentialSelector:
    def __init__(self, cls, sync):
        self._node = -1
        self.cls = cls
        self._sync = sync
        self._lock = threading.Lock()

    def selection(self):
        return spystat.statCluster(self._sync.dump())

    def candidates(self):
        result = filter(lambda x: x['syncing']['status'] == 'ok', self.selection())
        return map(lambda x: x['syncing']['url'], result)

    def select(self, selection=None):
        self._lock.acquire()
        self._node += 1
        if self._node >= len(self.cls):
            self._node = 0
        self._lock.release()

        infos = selection or spystat.statCluster(self._sync.dump())
        info = None
        for i in range(self._node, len(infos)):
            if infos[i]['syncing']['status'] == 'ok':
                info = infos[i]
                break
        if not info:
            for i in range(0, self._node):
                if infos[i]['syncing']['status'] == 'ok':
                    info = infos[i]
                    break
        if not info:
            return None
        return self.cls[self._node]

if __name__ == '__main__':
    import os, sys, time
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    from _clusters.leo import cls

    cls.setTimeout(1)
    s = Selector(cls)
    for i in xrange(0, 10000):
        client = s.select()
        if client:
            print client.url
        else:
            print 'No client'
        time.sleep(1)
    print 'done'
