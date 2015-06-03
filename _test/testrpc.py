#coding:utf-8

from helper import *
from core.client import Client
from core.cluster import Cluster

class TestRpc(unittest.TestCase):
    def testClient(self):
        cls = Client('127.0.0.1/leo', keysPath + 'leo.pem')
        cls.setHttpOpt({'timeout': 2})
        assert str(cls).startswith('''['ok', ['apiEcho',''')
        self.assertRaises(core.client.RpcApiNotFound, str, cls.abc)
        assert str(cls.apiEcho) == '''{'doc': 'For test.', 'params': ['msg'], 'name': 'apiEcho'}'''
        self.assertRaises(core.client.RpcBadParams, cls.apiEcho)

    def testCluster(self):
        cls = Cluster(keysPath + 'leo.pem')
        cls._load('127.0.0.1/storage/0')
        cls._load('127.0.0.1/storage/1')
        cls._load('127.0.0.1/storage/2')
        cls.setHttpOpt('timeout', 2)
        assert str(cls).startswith('''['ok', ['apiEcho',''')
        self.assertRaises(core.cluster.RpcApiNotFound, str, cls.abc)
        assert str(cls.apiEcho) == '''{'doc': 'For test.', 'params': ['msg'], 'name': 'apiEcho'}'''
        assert cls.apiEcho() == [['RpcBadParams', 'apiEcho'], ['RpcBadParams', 'apiEcho'], ['RpcBadParams', 'apiEcho']]

if __name__ == "__main__":
    unittest.main()
