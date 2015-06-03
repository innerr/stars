#coding:utf-8
#nature@20100804

import time
import hashlib

class Sessions:
    def __init__(self, auth, noAuthApis):
        self._auth = auth
        self._conns = {}
        self._noAuthApis = dict((api, True) for api in noAuthApis)
        self._autoClearInterval = 0
        self._autoClearCounter = 0
        self._max = 1024 * 1024

    def getConn(self, stub):
        conn = self._conns.get(stub)
        if not conn:
            return None
        return stub, conn[0], str(conn[1]), conn[2]

    def buildByTtl(self, caller, plaintext, ciphertext, apis, ttl):
        return self._build(caller, plaintext, ciphertext, apis, TtlCounter(ttl))

    def buildByExpire(self, caller, plaintext, ciphertext, apis, minu):
        return self._build(caller, plaintext, ciphertext, apis, ExpireCounter(minu))

    def clearOneStub(self, stub):
        conn = self._conns.get(stub)
        if not conn:
            return 'stubNotExists', stub
        self.release(stub)
        return 'ok', stub

    def auth(self, stub, api, caller = 'anonymous'):
        self._autoClear()
        api, params = self._parseApi(api)
        if self._noAuthApis.get('*'):
            return 'ok', caller
        if api in self._noAuthApis:
            return 'ok', caller
        if not stub or stub == 'None':
            return 'stubRequired', stub
        if not isinstance(stub, str):
            return 'stubBadFormat', stub
        conn = self._conns.get(stub)
        if not conn:
            return 'stubNotExists', stub
        apis, counter, caller = conn

        signature = apis.get(api)
        if signature == None:
            signature = apis.get('*')
        if signature == None:
            return 'apiCallDeny', caller
        for k, v in signature.items():
            cv = params.get(k)
            if cv[0] not in v:
                return 'apiParamDeny', caller

        result = counter.check()
        if result != 'ok':
            self.release(stub)
        return result, caller

    def release(self, stub):
        self._conns.pop(stub)

    def stubSize(self):
        return len(self._conns)

    def getMax(self):
        return self._max

    def setMax(self, max):
        self._max = max

    def clear(self):
        for k, v in self._conns.items():
            apis, counter, caller = v
            if not counter.peek():
                self._conns.pop(k)

    def releaseAll(self):
        self._conns.clear()

    def getAutoClearInterval(self):
        return self._autoClearInterval

    def setAutoClearInterval(self, interval):
        self._autoClearInterval = interval

    def _build(self, caller, plaintext, ciphertext, apis, counter):
        if self._max < len(self._conns):
            return 'reachedMaxCount'
        result = self._auth.auth(plaintext, ciphertext)
        if result != 'ok':
            return result
        apis = self._parseApis(apis)
        sha1 = hashlib.sha1()
        sha1.update(str(id(counter)))
        sha1.update(caller)
        sha1.update(str(time.time()))
        stub = sha1.hexdigest()
        if self._conns.has_key(stub) and self._conns[stub][2] != caller:
            return 'stubConflict'
        self._conns[stub] = (apis, counter, caller)
        return 'ok', stub

    def _autoClear(self):
        if self._autoClearInterval == 0:
            self.clear()
            return
        if self._autoClearInterval < 0:
            return
        self._autoClearCounter = self._autoClearCounter + 1
        if self._autoClearCounter > self._autoClearInterval:
            self.clear()
            self._autoClearCounter = 0

    def _parseApis(self, apis):
        apiDict = {}
        for api in apis.split(','):
            fun, params = self._parseApi(api)
            apiDict[fun] = params
        return apiDict

    def _parseApi(self, api):
        sig = api.split('|')
        fun = sig[0]
        params = {}
        for it in sig[1:]:
            i = it.find('=')
            if i < 0:
                params[it] = None
            else:
                values = it[i + 1:].split(':')
                params[it[:i]] = values
        return fun, params

class TtlCounter:
    def __init__(self, ttl):
        self._ttl = ttl

    def peek(self):
        return self._ttl > 0

    def check(self):
        if self._ttl <= 0:
            return 'ttl0'
        self._ttl = self._ttl - 1
        return 'ok'

    def __str__(self):
        return 'counter:' + str(self._ttl)

class ExpireCounter:
    def __init__(self, minu):
        self._expired = int(minu) * 60 + int(time.time())

    def peek(self):
        timestamp = int(time.time())
        if timestamp > self._expired:
            return False
        return True

    def check(self):
        return self.peek() and 'ok' or 'expired'

    def __str__(self):
        return 'expired:' + str(self._expired)
