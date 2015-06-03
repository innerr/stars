#coding:utf-8
#nature@20100725

import json
import urllib

# TODO Wrong if path is not 2 levels
def getApi(path):
    if  path.endswith('/'):
        i = path.rfind('/', 0, -1)
        return path[i + 1:-1].encode('ascii')
    else:
        i = path.rfind('/')
        return path[i + 1:].encode('ascii')

def unpack(queryString):
    params = {}
    if queryString is None:
        return params
    for pair in queryString.split('&'):
        if len(pair) > 0:
            values = pair.split('=')
            l = len(values)
            if l == 1:
                key, value = pair, None
            elif l == 2:
                key, value = values
            else:
                key, value = values[0], pair[len(values[0]) + 1:]
            params[key.encode('ascii')] = urllib.unquote_plus(value) if value else ''
    return params

def decode(response):
    if response == None:
        response = None
    elif isinstance(response, str) or isinstance(response, unicode):
        response = response.encode('utf8')
    elif isinstance(response, int) or isinstance(response, long) or isinstance(response, float):
        response = response
    elif isinstance(response, list) or isinstance(response, tuple):
        for i in range(0, len(response)):
            response[i] = decode(response[i])
    elif isinstance(response, dict):
        copy = {}
        for k, v in response.items():
            copy[k.encode('utf8')] = decode(v)
        response = copy
    else:
        raise Exception('Can not decode: type(%s), value(%s)' % (type(response).__name__, str(response)))
    return response

def pack(response, debug = 0):
    ctype = 'json'
    if (isinstance(response, list) or isinstance(response, tuple)) \
       and len(response) > 1 \
       and isinstance(response[0], str) \
       and response[0].startswith('type:'):
        ctype = response[0][5:]
        assert len(response) == 2
        response = response[1]
    elif response is None:
        response = ''
    elif ctype == 'json':
        response = dumps(response, debug)
    rtype = {
        'stream': 'application/octet-stream',
        'json': 'text/plain;charset=utf-8;ext=json',
        'plain': 'text/plain;charset=utf-8',
        'html': 'text/html;charset=utf-8',
    }[ctype]
    size = len(response)
    return [('Content-Type', rtype), ('Content-Length', str(size))], response, size

def dumps(response, debug = 0):
    if not (isinstance(response, tuple) or isinstance(response, list) or isinstance(response, set) or isinstance(response, dict)):
        response = [response]
    if debug:
        return json.dumps(response, indent = 4)
    return json.dumps(response)
