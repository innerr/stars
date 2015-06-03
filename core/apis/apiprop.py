#coding:utf-8
#nature@20100725

def propGet(env, key):
    'Get prop.'
    return 'ok', env.props.get(key)

def propSet(env, key, value):
    'Set prop.'
    env.props.set(key, value)
    env.props.save()
    return 'ok'
