#coding:utf-8
#nature@20100804

import os
import time
import base64

from Crypto.PublicKey import RSA 
from Crypto.Hash import MD5
from Crypto import Random

class TrustServer:
    def __init__(self, path, tolerate=600):
        self._tolerate = tolerate
        self._publics = []
        self.loaded = []
        if os.path.isfile(path):
            self._load(path)
        else:
            for root, dirs, files in os.walk(path):
                for file in files:
                    self._load(os.path.join(root, file))

    def auth(self, plaintext, signature):
        if not plaintext.isdigit():
            return 'plaintextBadFormat'
        timestamp = int(plaintext)
        now = int(time.time())
        if now - timestamp > self._tolerate:
            return 'timestampNotMatch', {'serverTime': str(now)}
        hash_str = MD5.new(plaintext).digest()
        for key in self._publics:
            try:
                if key.verify(hash_str, (long(signature),)):
                    return 'ok'
            except Exception, e:
                print 'stars.trust.auth', e
        return 'authFailed', plaintext, signature 

    def _load(self, file):
        if file.endswith('pem') or file.endswith('key'):
            self._publics.append(RSA.importKey(open(file).read()))
            self.loaded.append(os.path.basename(file))

class TrustClient:
    def __init__(self, file):
        self._private = RSA.importKey(open(file).read())

    def createAuth(self):
        plaintext = str(int(time.time()))
        hash_str = MD5.new(plaintext).digest()
        rng = Random.new().read
        signature = self._private.sign(hash_str, rng)    
        return plaintext, signature[0] 

if __name__ == '__main__':
    import pdb
    pdb.set_trace()
    s = TrustServer('_keys/leo.public.pem')
    c = TrustClient('_keys/leo.private.pem')
    p, sig = c.createAuth()
    print p, sig, s.auth(p, sig)
