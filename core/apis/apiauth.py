#coding:utf-8
#nature@20100725

def authBuildByTtl(env, caller, plaintext, ciphertext, apis, ttl):
    'Establish a connection by authentication, auto destroy after ttl time(s) api call. eg: fun1|id=8|file=myfile,*|id=7.'
    return env.auth.buildByTtl(caller, plaintext, ciphertext, apis, int(ttl))

def authBuildByExpire(env, caller, plaintext, ciphertext, apis, minu):
    'Establish a connection by authentication, auto destroy after specify minus. eg: fun1|id=8|file=myfile,*|id=7.'
    return env.auth.buildByExpire(caller, plaintext, ciphertext, apis, int(minu))

def authVerify(env, stub, api):
    'Check specify api can be called. api is a formatted string like: fun1|id=8|file=myfile.'
    return env.auth.auth(stub, api)

def authGetMax(env):
    'Get max number of stubs.'
    return 'ok', env.auth.getMax()

def authGetConnection(env, stub):
    conn = env.auth.getConn(stub)
    if not conn:
        return 'stubNotExists', stub
    return 'ok', conn

def authSetMax(env, max):
    'Set max number of stubs.'
    env.auth.setMax(int(max))
    return 'ok'

def authGetSize(env):
    'Get count of stubs.'
    return 'ok', env.auth.stubSize()

def authClearStub(env):
    'Clear expired stubs.'
    env.auth.clear()
    return 'ok'

def authReleaseAll(env):
    'Clear all stubs.'
    env.auth.releaseAll()
    return 'ok'

def authGetAutoClearInterval(env):
    'Get auto clear period.'
    return 'ok', env.auth.getAutoClearInterval()

def authSetAutoClearInterval(env, interval):
    'Set auto clear period. 0=every time, -1=disabled.'
    env.auth.setAutoClearInterval(int(interval))
    return 'ok'

def authClearOneStub(env, stub):
    'For clear one stub'
    return env.auth.clearOneStub(stub)
