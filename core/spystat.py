#coding:utf-8
#nature@20100825

import time
import bisect
import synchro

def statCluster(datas, minu=5, freqsName='freqs', recordsName='records'):
    return map(lambda x: statClient(x, minu, freqsName, recordsName), datas)

def statClient(data, minu=5, freqsName='freqs', recordsName='records'):
    now = 60 * int(time.time() / 60)
    filter = lambda d, m: d[bisect.bisect(map(lambda x: x[0], d), now - m * 60):]
    freqs = filter(data.pop(freqsName) or [], minu)
    records = filter(data.pop(recordsName) or [], minu)
    data['summary'] = {}

    start, end = _statTime(freqs, records)
    data['syncing'].update({'startTime': start, 'endTime': end})

    summary1, result1 = _statFreqs(freqs)
    data[freqsName] = result1
    data['summary'].update(summary1)

    summary2, result2 = _statRecords(records)
    _calAvg(summary2)
    _calAvg(result2)
    data[recordsName] = result2
    data['summary'].update(summary2)
    return data

def _statTime(freqs, records):
    start1 = len(freqs) > 0 and freqs[0][0] or -1
    start2 = len(records) > 0 and records[0][0] or -1
    if start1 < 0:
        start = start2
    else:
        start = start2 > 0 and min(start1, start2) or start1
    return start, 60 * int(time.time() / 60)

def _statFreqs(freqs):
    summary = {'core.event.cnt': 0, 'event.cnt': 0}
    result = {}
    for it in freqs:
        timestamp, kv = it
        for k, v in kv.items():
            result[k] = result.get(k) or 0 + v
            summary[k.startswith('core.') and 'core.event.cnt' or 'event.cnt'] += v
    return summary, result

def _statRecords(records):
    result = {}
    summary = {}
    sumKeys = ['core.api.cost', 'core.api.out', 'api.cost', 'api.out']
    for it in sumKeys:
        summary[it] = {'max': 0, 'sum': 0, 'cnt': 0}
    for it in records:
        timestamp, kv = it
        for k, v in kv.items():
            if not result.has_key(k):
                result[k] = {'max': 0, 'sum': 0, 'cnt': 0}
            _plus(result[k], v)
            for it in sumKeys:
                if k.startswith(it):
                    _plus(summary[it], v)
                    break
    return summary, result

def _plus(s, v):
    s['max'] = max(s['max'], v['max'])
    s['sum'] += v['sum']
    s['cnt'] += v['count']

def _calAvg(data):
    for k, v in data.items():
        v['avg'] = int(v.pop('sum') / (v['cnt'] or 1))

if __name__ == '__main__':
    import os
    import init
    import daemons
    import cluster

    key = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + '/_keys/private/leo.pem'
    cls = cluster.Cluster(key).load('127.0.0.1/leo').load('227.0.0.1/leo')
    tasks = daemons.Daemons()

    sync = synchro.ClusterSync(cls, tasks)
    sync.add('records', synchro.SpySyncer(10, 'spyGetRecords'))
    sync.add('freqs', synchro.SpySyncer(10, 'spyGetFreqs'))
    sync.thread('values').add('auth.size', synchro.ValueSyncer('authGetSize'))
    sync.thread('values').add('spy.max', synchro.ValueSyncer('spyGetMax'))
    sync.start(1)

    for i in range(0, 100):
        datas = statCluster(sync.dump(), 5)
        for data in datas:
            syncing = data['syncing']
            summary = data['summary']
            values = data['values']
            print syncing['url']
            print '\t', syncing['status'], 'core{', summary['core.api.cost'], summary['core.event.cnt'], '}  apis{', summary['api.cost'], summary['event.cnt'], '}'
            print '\t', values.get('auth.size'), values.get('spy.max')
        print
        time.sleep(3)
    sync.stop()
    print 'Done'
