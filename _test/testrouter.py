#coding:utf-8

import time
from helper import *
from core.cluster import Cluster
from router.client import StorageClient

class TestRouter(unittest.TestCase):
    def testRouter(self):
        stg = Cluster(keysPath + 'leo.pem')
        stg._load('127.0.0.1/storage/0')
        stg._load('127.0.0.1/storage/1')
        stg._load('127.0.0.1/storage/2')
        stg._load('127.0.0.1/storage/3')
        assert stg[0].format(0) == ['ok']
        assert stg[1].format(1) == ['ok']
        assert stg[2].format(2) == ['ok']
        assert stg[3].format(3) == ['ok']

        cls = StorageClient('127.0.0.1/router/0', keysPath + 'leo.pem')        
        cls.readers()
        time.sleep(0.5)

        assert len(cls.readers()[1]) == 4
        assert len(cls.writers()[1]) == 4

        content = 'test1234'
        for i in range(0, 1):
            ok, id = cls._write(content)
            assert ok == 'ok'
            assert cls._read(id) == content
            print cls._read(id, 1).read()

if __name__ == "__main__":
    unittest.main()
