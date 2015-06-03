#coding:utf-8
#nature@20100805

import rpc

class CoreCaller:
    def __init__(self, url):
        #url = '127.0.0.1' + (url.startswith('/') and '' or '/') + url
        self._apis = rpc.RemoteApiCube(url)

class FakeSpy():
    def __init__(self, *args, **kwargs):pass
    def increase(self, key):pass
    def record(self, key, value):pass

class Spy(CoreCaller):
    def increase(self, key):
        self._apis.call('spyIncrease', key = key)

    def record(self, key, value):
        self._apis.call('spyRecord', key = key, value = value)

class Auth(CoreCaller):
    def __init__(self, url, noAuthApis):
        CoreCaller.__init__(self, url)
        self._noAuthApis = noAuthApis

    def auth(self, stub, api):
        if api.split('|')[0] in self._noAuthApis:
            return 'ok', None
        result = self._apis.call('authVerify', stub = stub, api = api)
        assert isinstance(result, list) or isinstance(result, tuple)
        return result

    def buildByTtl(self, caller, plaintext, ciphertext, apis, ttl):
        return self._apis.call('authBuildByTtl', caller = caller, plaintext = plaintext, ciphertext = ciphertext, apis = apis, ttl = ttl)

    def buildByExpire(self, caller, plaintext, ciphertext, apis, minu):
        return self._apis.call('authBuildByExpire', caller = caller, plaintext = plaintext, ciphertext = ciphertext, apis = apis, minu = minu)

    def clearOneStub(self, stub):
        return self._apis.call('authClearOneStub', stub = stub)

class Props(CoreCaller):
    def set(self, key, value):
        return self._apis.call('propSet', key = key, value = value)

    def get(self, key):
        result = self._apis.call('propGet', key = key)
        assert isinstance(result, list) or isinstance(result, tuple)
        assert result[0] == 'ok'
        return result[1]
