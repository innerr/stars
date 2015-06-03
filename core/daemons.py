#coding:utf-8
#nature@20100904

import daemon

class Daemons:
    def __init__(self):
        self._tasks = {}
 
    def __del__(self):
        self.terminate(0)

    def run(self, name, callback, interval, args={}):
        queue = self._tasks.get(name)
        if queue == None:
            queue = []
            self._tasks[name] = queue
        task = daemon.Daemon()
        queue.append(task)
        task.start(callback, interval, args)
        return True

    def running(self):
        tasks = []
        for k, v in self._tasks.items():
            if v:
                tasks.append(k)
        return tasks

    def started(self, name):
        task = self._tasks.get(name)
        if not task:
            return False
        return len(task) > 0

    def stop(self, name):
        if not self._tasks.has_key(name):
            return
        map(lambda x: x.terminate(0), self._tasks.pop(name))

    def terminate(self, timeout=10):
        for name in list(self._tasks):
            map(lambda x: x.terminate(timeout), self._tasks.pop(name))

if __name__ == '__main__':
    import time
    class Callback:
        def __init__(self, data):
            self._data = data
        def __call__(self):
            print 'Callling:', self._data
    tasks = Daemons()
    tasks.run('task1', Callback('Hi from task1'), 1)
    tasks.run('task2', Callback('Hi from task2'), 1)
    print 'Running', tasks.running()
    time.sleep(1)
    tasks.stop('task2')
    print 'Stop task2'
    time.sleep(1)
    tasks.stop('task1')
    print 'Stop all'
    tasks.terminate()
    time.sleep(1)
    print 'Done'
