#coding:utf-8
#nature@20100725

import os
import time
import traceback
import copy

import init
import argstool
import packer
import fcgi
import wsgi
import cube
import trust
import prop
import config
import daemons
import logger

# 'xtornado' is a modified version of tornado，for chunked transfer supported.
_ASYNC_HTTP_SUPPORT_SERVER = 'xtornado'

def run(*args):
    try:
        args = argstool.mix2py(args)
    except:
        traceback.print_exc()
        _help()
        return
    if 'help' in list(args):
        _help()
        return
    args = _prepare(args)

    app = args['inner'] and _buildCore(args) or _buildApis(args)
    app.supportAsyncHTTP = args.get('server') == _ASYNC_HTTP_SUPPORT_SERVER
    _buildApp(args, app)
    _prompt(args)
    app.apis.initModule(app)
    _runServer(args, entry, app)
    app.apis.finalizeModule(app)
    app.tasks.terminate()

def _prompt(args):
    print 'Run {'
    for k, v in args.items():
        if isinstance(v, list) and len(v) > 1:
            print '\t' + k + ':'
            for it in v:
                print '\t\t' + it
        elif isinstance(v, dict) and len(v) > 1:
            print '\t' + k + ':'
            for n, d in v.items():
                print '\t\t' + n + ':', d
        else:
            print '\t' + k + ':', v
    print '} ...'

def _help():
    print 'Core mode: run port=n keys=path [options]'
    print 'Apis mode: run port=n core=url path=p1,p2 [-path=p1,p2] [mode=t|p] [options]'
    print 'Hybrid mode: run port=n keys=path [options] path=core-path,p1,p2 [-path=p1,p2] [mode=t|p] [options]'
    print 'Options: [debug=0|1] [flup={k1=v1,k2=v2,}] [args={k1=v1,k2=v2,}]'

def _prepare(args):
    'Refine args.'
    default = {
        'port': '0',
        'mode': 't',
        'debug': '0',
        'config': '',
        'configPath': '',
        'noauth': [],
        'flup': {},
        'args': {},
        'path': [],
        '-path': [],
    }
    default.update(args)
    args = default
    core = os.path.dirname(__file__)
    base = os.path.dirname(core)
    args['corePath'] = core
    args['basePath'] = base
    args['path'] = isinstance(args['path'], str) and [args['path']] or args['path']
    args['-path'] = isinstance(args['-path'], str) and [args['-path']] or args['-path']
    args['path'] = map(lambda path: os.path.abspath(path), args['path'])
    args['-path'] = map(lambda path: os.path.abspath(path), args['-path'])
    args['inner'] = core in args['path']
    args['hybrid'] = args['inner'] and len(args['path']) > 1
    args['noauth'] = ['apiList', 'apiInfo', 'apiEcho', 'apiPublic'] + (isinstance(args['noauth'], str) and [args['noauth']] or args['noauth'])
    args['noauth'] = filter(lambda x: len(x) != 0, args['noauth'])
    return args

class Obj: pass
class Globals(dict):
    def __init__(self):
        dict.__init__(self)

    def __getattr__(self, key):
        if self.has_key(key):
            return self.get(key, None)

def _buildApp(args, app):
    app.debug = args['debug'] == '1'
    app.args = args['args']
    app.tasks = daemons.Daemons()
    app.globals = Globals()

def _buildCore(args):
    'Build core application.'
    assert args['mode'] == 't', 'Core or hybrid mode must run at threading mode.'
    import session
    import spy
    app = Obj()
    app.inner = True
    app.spy = spy.Spy()
    app.apis = cube.ApiCube(args['path'], args['-path'], args['corePath'])
    app.config = config.Config(args['configPath'])
    trustServer = trust.TrustServer(args['keys'])
    app.auth = session.Sessions(trustServer, args['noauth'] + ['authBuildByTtl', 'authBuildByExpire', 'authVerify'])
    app.props = prop.Props()
    app.logger = logger.ErrLogger('log', 'core_' + args['port'] + "_" + str(os.getpid()))
    print 'Loaded', trustServer.loaded
    return app

def _buildApis(args):
    'Build apis application.'
    assert args.get('core'), 'Apis mode must specify core url.'
    import bridge
    import core.apis.apiapi
    import core.apis.apiauth
    app = Obj()
    app.inner = False
    if args.get('spy', 'True').lower() == 'true':
        app.spy = bridge.Spy(args['core'])
    else:
        app.spy = bridge.FakeSpy(args['core'])
    app.apis = cube.ApiCube(args['path'], args['-path'] + [args['corePath']], None)
    app.config = config.Config(args['configPath'])
    app.auth = bridge.Auth(args['core'], args['noauth'] + ['authBuildByTtl', 'authBuildByExpire'])
    app.apis.loadModule(core.apis.apiapi)
    app.apis.loadFunction(core.apis.apiauth.authBuildByTtl, None, True)
    app.apis.loadFunction(core.apis.apiauth.authBuildByExpire, None, True)
    app.apis.loadFunction(core.apis.apiauth.authClearOneStub, None, True)
    app.props = bridge.Props(args['core'])
    app.logger = logger.ErrLogger('log', 'core_' + args['port'] + "_" + str(os.getpid()))
    return app

def entry(environ, app):
    now = time.time()
    env, spy = _buildEnv(environ, app)
    response = _invoke(env, spy)
    try:
        headers, response, size = packer.pack(response, env.debug)
        if env.headers:
            headers.extend(env.headers)
        spy.record('api.out.' + env.req.api, size)
        spy.record('api.cost.' + env.req.api, int((time.time() - now) * 1000))
    except:
        headers, response, size = packer.pack(('type:plain', traceback.format_exc()), env.debug)
    return headers, response

def _invoke(env, spy):
    try:
        authResult, caller = _auth(env)
        if authResult == 'api':
            spy.logger.log('deny???')
        env.req.caller = caller
        if authResult != 'ok':
            spy.increase('warn.' + authResult)
            return authResult
        return env.apis.call(env.req.api, env.req.args, env)
    except cube.ApiCube.ApiNotExists, e:
        spy.increase('warn.apiNotFound')
        return 'apiNotFound', str(e)
    except cube.ApiCube.ApiBadParams, e:
        spy.increase('warn.badParams.' + env.req.api)
        return 'badParams', str(e)
    except Exception, e:
        spy.increase('exception.' + env.req.api + '.' + type(e).__name__)
        traceInfo = traceback.format_exc()
        spy.logger.log(traceInfo)
        if env.debug:
            return 'type:plain', traceInfo
        return 'serverError', type(e).__name__ + str(e.args) + ', traceinfo: ' + traceInfo

def _buildEnv(environ, app):
    env = copy.copy(app)
    req = Obj()
    req.ip = environ['REMOTE_ADDR']
    req.post = environ['wsgi.input']
    req.method = environ['REQUEST_METHOD']
    req.type = environ.get('CONTENT_TYPE', None)
    req.length = environ.get('CONTENT_LENGTH', None)
    req.api = packer.getApi(environ['PATH_INFO'])
    req.args = packer.unpack(environ.get('QUERY_STRING', None))
    if len(req.args) == 0 and req.method == 'POST' and req.type == 'application/x-www-form-urlencoded':
        req.args = packer.unpack(req.post.read())
    req.stub = req.args.has_key('_stub') and req.args.pop('_stub') or None
    env.req = req
    env.headers = None

    if app.inner:
        spy = Obj()
        spy.record = lambda k, v: app.spy.record('core.' + k, v)
        spy.increase = lambda k: app.spy.increase('core.' + k)
    else:
        spy = env.spy
    spy.logger = app.logger
    return env, spy

def _auth(env):
    api = env.req.api
    for k, v in env.req.args.items():
        api += '|' + str(k) + '=' + str(v)
    authResult, caller = env.auth.auth(env.req.stub, api)

    if authResult != 'ok': # and not (env.debug and env.inner and env.req.ip == '127.0.0.1'): #
        return authResult, caller
    return 'ok', caller

def _runServer(args, entry, app):
    if args.get('server') is None or args.get('server') == 'flup':
        fcgi.run(entry, app, int(args['port']), args['flup'], args['mode'] == 'p')
    else:
        server = getattr(wsgi, args.get('server'), None)
        server(entry, app, int(args['port']), args.get(args['server'], args))
