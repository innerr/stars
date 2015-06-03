#coding:utf-8
#nature@20100725

def spyGetFreqs(env, timestamp):
    'Read events frequency greater than specify timestamp.'
    return 'ok', env.spy.getGreaterFreqs(timestamp)

def spyGetRecords(env, timestamp):
    'Read value records greater than specify timestamp.'
    return 'ok', env.spy.getGreaterRecords(timestamp)

def spyGetMax(env):
    'Get spy max capacity.'
    return 'ok', env.spy.getMax()

def spySetMax(env, max):
    'Set spy max capacity.'
    env.spy.setMax(max)
    return 'ok'

def spyIncrease(env, key):
    'Record a event.'
    env.spy.increase(key)
    return 'ok'

def spyRecord(env, key, value):
    'Record a value.'
    env.spy.record(key, value)
    return 'ok'

