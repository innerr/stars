#coding:utf-8
#nature@20100904

import time
import threading

class Daemon:
    def __init__(self):
        self._thread = None
        self._event = threading.Event()

    def __del__(self):
        self.terminate(0)

    def start(self, callback, interval, args={}):
        def wrapper():
            return callback(**args)
        self._callback = wrapper
        self._args = args
        self._interval = interval
        if self._thread:
            return
        self._thread = threading.Thread(None, self._work, kwargs={'owner': threading.currentThread()})
        self._thread.start()

    def started(self):
        return self._thread != None

    def terminate(self, timeout=10):
        self._interval = -1
        self._event.set()
        self._event.clear()
        if timeout > 0:
            self._thread.join(timeout)
        self._thread = None

    def _work(self, owner):
        termed = lambda: self._interval == None or self._interval < 0
        while not termed():
            now = time.time()
            self._callback()
            if termed():
                break
            interval = self._interval - (time.time() - now)
            if interval > 0:
                self._event.wait(interval)
            if termed() or not owner.isAlive():
                break

if __name__ == '__main__':
    import time
    import urllib2
    def callback(msg):
        print 'In:', msg
        for i in range(0, 10):
            urllib2.urlopen('http://www.sina.com.cn')
        print 'Out:', msg
    task = Daemon()
    task.start(callback, 1, {'msg': 'Hi'})
    time.sleep(2)
    time.sleep(2)
    task.start(callback, 1, {'msg': 'Hello'})
    time.sleep(2)
    task.terminate()
    print 'Done'
