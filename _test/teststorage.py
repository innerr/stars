#coding:utf-8

from helper import *
from core.client import Client
from core.cluster import Cluster

class TestStorage(unittest.TestCase):
    def testStorage(self):
        cls = Client('127.0.0.1/storage/0', keysPath + 'leo.pem')
        cls.setHttpOpt({'timeout': 2})
        assert cls.format(1) == [ok]
        assert cls.info(0) == ['fileNotFound']
        assert cls.format(1) == [ok]
        assert cls.node() == [ok, 1]
        assert cls.write(_post='abc') == [ok, '%06d%024d' % (1, 0)]
        assert cls.size() == [ok, 1]
        assert cls.format(2) == [ok]
        assert cls.node() == [ok, 2]

        f2 = '%06d%024d' % (2, 0)
        assert cls.write(_post='abc') == [ok, f2]
        assert cls.info(f2)[0] == ok
        assert cls.info('%06d%024d' % (2, 200)) == ['fileNotFound']
        assert cls.read(f2) == 'abc'
        assert cls.read(f2, _lazy=1).read() == 'abc'
        assert cls.delete(f2) == [ok]
        assert cls.read(f2) == ''
        assert str(cls.info(f2)).startswith('''['ok', {'deleted': 1, 'dtime':''')

        toId = lambda x: '%06d%024d' % (1, x)
        assert cls.format(1) == [ok]
        for i in xrange(0, 5):
            assert cls.write(_post='abc') == [ok, toId(i)]
        assert cls.greater(toId(0), 3) == [ok, map(toId, [0, 1, 2])]
        assert cls.greater(toId(0), 5) == [ok, map(toId, [0, 1, 2, 3, 4])]
        assert cls.greater(toId(0), 6) == [ok, map(toId, [0, 1, 2, 3, 4])]
        assert cls.greater(toId(3), 6) == [ok, map(toId, [3, 4])]

        file = open(os.path.realpath(__file__), 'rb')
        result = cls.write(_post=file)
        file.close()
        assert result[0] == ok
        assert cls.read(result[1]).startswith('#coding:utf-8')

        assert cls.format(1) == [ok]

    def testCluster(self):
        cls = Cluster(keysPath + 'leo.pem')
        cls._load('127.0.0.1/storage/0')
        cls._load('127.0.0.1/storage/1')
        cls._load('127.0.0.1/storage/2')
        cls.setHttpOpt('timeout', 3)
        assert cls.format(1) == [[ok], [ok], [ok]]
        result = cls.write(_post='eee')
        assert len(result) == 3 and map(lambda x: x[0], result) == [ok, ok, ok], result
        assert cls.read(result[0][1]) == ['eee', 'eee', 'eee']
        assert cls.read(result[1][1]) == ['eee', 'eee', 'eee']
        assert cls.read(result[2][1]) == ['eee', 'eee', 'eee']
        result = cls.read(result[0][1], _lazy=1)
        assert len(result) == 3 and map(lambda x: str(x.size()) + x.read(), result) == ['3eee', '3eee', '3eee']

        file = open(os.path.realpath(__file__), 'rb')
        result = cls.write(_post=file)
        assert len(result) == 3 and map(lambda x: x[0], result) == [ok, ok, ok]
        file.close()
        result = cls.read(result[0][1], _lazy=1)
        assert map(lambda x: x.read(12), result) == ['#coding:utf-8', '#coding:utf-8', '#coding:utf-8']

if __name__ == "__main__":
    unittest.main()
