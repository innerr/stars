#coding:utf-8
#nature@20100725

from rpc import *

class RpcApiNotFound(Exception): pass
class RpcBadParams(Exception): pass

class Client:
    def __init__(self, url, keyFile, apis='*', value='60', mode='minu', caller='anonymous'):
        self._auth = AutoAuth(caller, url, keyFile, apis, value, mode)
        self._cube = AutoAuthApiCube(url, self._auth)
        self._apis = {}
        self.url = url
        self.setHttpOpt = self._cube.setHttpOpt
        self.stub = self._auth.stub
        self.newStub = self._auth.newStub
        self.help = lambda: str(self.__getattr__('apiList')())
        self.__str__ = self.help
        self.__repr__ = self.help

    def __getattr__(self, _api):
        if _api.startswith('_'):
            raise AttributeError, _api
        api = self._apis.get(_api)
        if not api:
            api = Api(self._cube, _api)
            self._apis[_api] = api
        return api

class Api:
    def __init__(self, caller, api):
        self._caller = caller
        self._api = api
        self._params = None
        self._doc = None

    def __call__(self, *v, **kv):
        params = self._getParams()
        for i in range(0, len(v)):
            kv[params[i]] = str(v[i])
        for param in params:
            if not kv.has_key(param):
                raise RpcBadParams(self._api + ": missed '%s' in params" % param)
        if kv.has_key('_post'):
            _post = kv['_post']
            kv.pop('_post')
            return self._caller.call(self._api, _post = _post, **kv)
        return self._caller.call(self._api, **kv)

    def help(self):
        if self._doc is None:
            result = self._caller.call('apiInfo', api=self._api)
            if not isinstance(result, list) or result[0] != 'ok':
                raise RpcFailed(result)
            self._doc = str(result[1])
            if self._doc == 'apiNotFound':
                raise RpcApiNotFound(self._api)
        return self._doc

    def __str__(self):
        return self.help()

    def __repr__(self):
        return self.help()

    def _getParams(self):
        if self._params is None:
            info = self._caller.call('apiInfo', api=self._api)
            if not info or not isinstance(info, list) or len(info) < 2 or info[0] != 'ok':
                raise RpcFailed(self._api, info)
            if info[1] == 'apiNotFound':
                raise RpcApiNotFound(self._api)
            self._params = info[1]['params']
        return self._params
