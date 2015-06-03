#coding:utf-8
#nature@20100725

import os
import urllib
import urllib2
import gzip
import json
import trust
import packer
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

class RpcFailed(Exception): pass
class RpcAuthFailed(Exception): pass

class RemoteApiCube:
    def __init__(self, url):
        assert not url.startswith('http'), 'Url format: host:port/path/'
        self._url = url.endswith('/') and url or (url + '/')
        self._httpOpt = {'protocol': 'http', 'timeout': 30, 'user-agent': 'ver-2.0'}
        self._opener = urllib2.build_opener()

    def getUrl(self):
        return self._url

    def setHttpOpt(self, opt):
        self._httpOpt.update(opt)
        old = self._httpOpt
        self._httpOpt = opt
        self._httpOpt.update(old)

    def redirect(self, url):
        assert not url.startswith('http'), 'Url format: host:port/path/'
        self._url = url.endswith('/') and url or (url + '/')

    def call(self, _api, _post = None, _lazy = 0, _method = 'GET', **params):
        params = params or {}
        headers = self._makeHeaders()
        timeout = self._httpOpt['timeout']
        if params.has_key('__timeout'):
            timeout = int(params['__timeout'])
            params.pop('__timeout')
        if _method == 'GET':
            qs = '&'.join([str(k) + '=' + urllib.quote_plus(str(v)) for k, v in params.items()])
#            for k, v in params.items():
#                qs += str(k) + '=' + urllib.quote_plus(str(v)) + '&'
            url = self._httpOpt['protocol'] + '://' + self._url + _api + '/?' + qs
        elif _method == 'POST':
            url = self._httpOpt['protocol'] + '://' + self._url + _api + '/'
            _post = urllib.urlencode(params)
            headers['Content-Type'] = 'application/x-www-form-urlencoded'

        request = urllib2.Request(url, self._postAdapter(_post), headers)
        request.add_header('Accept-encoding', 'gzip')
        try:
            stream = self._opener.open(request, timeout = timeout)
            info = stream.info()
            if info.get('Content-Encoding') == 'gzip':
                result = stream.read()
                stream.close()
                stream = gzip.GzipFile(fileobj = StringIO(result))
        except Exception, e:
            raise RpcFailed(self._url + _api, str(e))
        try:
            if 'ext=json' in info.getplist():
                result = packer.decode(json.load(stream))
            elif 'application/octet-stream' == info.gettype():
                size = info.get('content-length')
                if _lazy:
                    class Obj: pass
                    result = Obj()
                    result.__len__ = lambda: size
                    result.size = lambda: size
                    result.read = stream.read
                else:
                    result = stream.read()
            else:
                # 来到这个逻辑，是没有返回http头
                result = stream.read()
        except IOError, e:
            if e.message == 'Not a gzipped file':
                result = 'Not a gzipped file'
            else:
                result = str(e)
        except Exception, e:
            result = stream.read()

        if isinstance(result, str):
            try:result = json.loads(result)
            except:pass
            stream.close()
        return result

    def _makeHeaders(self):
        headers = {}
        agent = self._httpOpt.get('user-agent')
        if agent:
            headers['User-Agent'] = agent
        return headers

    @staticmethod
    def _postAdapter(post):
        if post is None:
            return post
        if hasattr(post, 'read') and not hasattr(post, 'len'):
            class Obj: pass
            clone = Obj()
            clone.read = post.read
            clone.__len__ = lambda: int(os.stat(post.name).st_size)
            return clone
        return post

class AutoAuthApiCube:
    def __init__(self, url, auth):
        self._auth = auth
        self._base = RemoteApiCube(url)

    def setHttpOpt(self, opt):
        self._auth.setHttpOpt(opt)
        self._base.setHttpOpt(opt)

    def call(self, _api, _post = None, **params):
        params = params or {}
        params['_stub'] = self._auth.stub()
        result = self._base.call(_api, _post, **params)
        # TODO
        if isinstance(result, list) and len(result) > 0 and (result[0] == 'stubNotExists' or result[0] == 'apiCallDeny'):
            params['_stub'] = self._auth.renew()
            result = self._base.call(_api, _post, **params)
        return result

class AutoAuth:
    def __init__(self, caller, url, keyFile, apis = '*', value = '60', mode = 'minu'):
        self._keyFile = keyFile
        self._mode = mode
        self._value = value
        self._apis = apis
        self._base = RemoteApiCube(url)
        self._stub = None
        self._caller = caller
        self.setHttpOpt = self._base.setHttpOpt

    def stub(self):
        if not self._stub:
            self._stub = self.create(self._base, self._caller, self._keyFile, self._apis, self._value, self._mode)
        return self._stub

    def renew(self):
        self._stub = None
        return self.stub()

    def newStub(self, apis = '*', value = '60', mode = 'minu', caller = 'anonymous'):
        return self.create(self._base, caller, self._keyFile, apis, value, mode)

    @staticmethod
    def create(core, caller, keyFile, apis, value, mode):
        plaintext, ciphertext = trust.TrustClient(keyFile).createAuth()
        if mode == 'minu':
            params = {'caller': caller, 'plaintext': plaintext, 'ciphertext': ciphertext, 'apis': apis, 'minu': value}
            result = core.call('authBuildByExpire', **params)
        else:
            params = {'caller': caller, 'plaintext': plaintext, 'ciphertext': ciphertext, 'apis': apis, 'ttl': value}
            result = core.call('authBuildByTtl', **params)
        if not result or len(result) < 2:
            raise RpcAuthFailed(result, core._url)
        if not (isinstance(result, list) and result[0] == 'ok'):
            raise RpcAuthFailed(result, core._url)
        return result[1]

if __name__ == '__main__':
    request = urllib2.Request('https://10.20.187.112/7015/syncFile/?_stub=17016663e436d9505fbcb077ac7f8f931870c38e&opver=0&size=512&')
    #request = urllib2.Request('https://10.20.187.112/7000/detail?cluster=leo.s0&reload=3&minu=5')
    request.add_header('Accept-encoding', 'gzip')
    response = urllib2.urlopen(request)
    print response.info()
    if response.headers.get('Content-Encoding') == 'gzip':
        buf = StringIO(response.read())
        f = gzip.GzipFile(fileobj = buf)
        data = f.read()
        print 'end', len(data)
    else:
        print response.read()
