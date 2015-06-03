#coding:utf-8
#nature@20100820

import client
import threading
from client import *

class Clients:
    def __init__(self):
        self._httpOpt = {'protocol': 'http', 'timeout': 3, 'user-agent': 'stars-rpc-client', 'keep-alive': True}
        self.setHttpOpt = self._httpOpt.__setitem__
        self._cls = {}
        self.__len__ = self._cls.__len__
        self.__getitem__ = lambda i: self._cls.values().__getitem__(i)
        self._get = self._cls.__getitem__
        self._remove = lambda url: self._cls.has_key(url) and self._cls.pop(url)
        self.__repr__ = lambda: len(self._cls) > 0 and str(self._cls.values()[0]) or ''
        self.__str__ = self.__repr__

    def _add(self, cls):
        cls.setHttpOpt(self._httpOpt)
        self._cls[cls.url] = cls

    def __getattr__(self, _api):
        if _api.startswith('__'):
            raise AttributeError, _api
        apis = Apis()
        for url, cls in self._cls.items():
            apis.add(getattr(cls, _api))
        return apis

class Cluster(Clients):
    def __init__(self, keyFile, apis='*', 
                 value='60', mode='minu', 
                 caller='anonymous'):
        Clients.__init__(self)
        self._opts = (keyFile, apis, value, mode, caller)

    def _load(self, url, keyFile = None):
        if keyFile:
            assert isinstance(keyFile, str)
            tempOpts = list(self._opts)
            tempOpts[0] = keyFile
            self._opts = tempOpts

        self._add(client.Client(url, *self._opts))
        return self

    def _loads(self, hosts, path):
        for host in hosts:
            self._add(client.Client(host + '/' + path, *self._opts))
        return self

class Apis:
    def __init__(self):
        self._apis = []
        self.add = self._apis.append
        self.__repr__ = lambda: len(self._apis) > 0 and str(self._apis[0]) or ''
        self.__str__ = self.__repr__

    def __call__(self, *v, **kv):
        _post = kv.get('_post')
        results = []
        for i in range(0, len(self._apis)):
            if _post and hasattr(_post, 'read') and hasattr(_post, 'seek'):
                _post.seek(0)
            try:
                results.append(self._apis[i](*v, **kv))
            except Exception, e:
                results.append([type(e).__name__ , str(e)])
        return results
