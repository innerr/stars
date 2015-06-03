#coding:utf-8
#nature@20100725

def apiList(env):
    'List all api(s).'
    apis = env.apis.apiList()
    apis.sort()
    return 'ok', apis

def apiPublic(env):
    'List public api(s)'
    apis = env.apis.apiPublic()
    return 'ok', apis

def apiInfo(env, api):
    'Get infomation of a specify api.'
    return 'ok', env.apis.apiInfo(api) or 'apiNotFound'

def apiEcho(env, msg):
    'For test.'
    return 'ok', msg

