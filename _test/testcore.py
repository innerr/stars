#coding:utf-8

from helper import *
from core.client import Client

class TestCore(unittest.TestCase):
    def testCore(self):
        c = Client('10.20.134.71/7002', keysPath + 'leo.private.pem')
        c.setHttpOpt({'timeout': 2})
        #print c.apiList()
        #assert str(c.apiList()).startswith('''['ok', ['apiEcho',''')
        assert str(c.apiInfo('apiEcho')) == '''['ok', {'doc': 'For test.', 'params': ['msg'], 'name': 'apiEcho'}]'''
        assert c.apiEcho('hi') == [ok, 'hi']

        c.spySetMax(123)
        assert c.spyGetMax() == [ok, 123]
        c.spySetMax(321)
        assert c.spyGetMax() == [ok, 321]
        c.authSetMax(123)
        assert c.authGetMax() == [ok, 123]
        c.authSetMax(321)
        assert c.authGetMax() == [ok, 321]
        c.authSetAutoClearInterval(123)
        assert c.authGetAutoClearInterval() == [ok, 123]
        c.authSetAutoClearInterval(321)
        assert c.authGetAutoClearInterval() == [ok, 321]

        c.propSet('k1', 'v1')
        assert c.propGet('k1') == [ok, 'v1']
        c.propSet('k2', 'v2')
        assert c.propGet('k1') == [ok, 'v1']
        assert c.propGet('k2') == [ok, 'v2']
        c.propSet('k1', 'v2')
        assert c.propGet('k1') == [ok, 'v2']
        c.propSet('k2', 'v1')
        assert c.propGet('k2') == [ok, 'v1']

        assert c.authClearStub() == [ok]
        assert c.authReleaseAll() == [ok]
        #assert c.authGetSize() == [ok, 0]

        d = Client('10.20.134.71/7002', keysPath + 'leo.private.pem', apis='spyGetMax', mode='ttl', value='1')
        d.setHttpOpt({'timeout': 2})
        assert d.apiEcho('hi') == [ok, 'hi']
        #assert c.authGetSize() == [ok, 1]

        assert c.authVerify('dd', 'spyGetMax') == ['stubNotExists', 'dd'] 
        assert d.spyGetMax()[0] == ok
        #assert d.authVerify(d.stub(), 'spySetMax') == ['apiCallDeny']
        #assert d.authVerify(d.stub(), 'spyGetMax') == ['ttl0'] 
        assert c.authClearStub() == [ok]
        #assert d.authVerify(d.stub(), 'spyGetMax')[0] == 'stubNotExists'

        assert c.spyIncrease('k1') == [ok]
        assert c.spyRecord('k1', 10) == [ok]

        assert c.spyGetFreqs(int(time.time()))[0] == ok
        assert c.spyGetRecords(int(time.time()))[0] == ok
        print '[Stars] OK!'

if __name__ == "__main__":
    unittest.main()
