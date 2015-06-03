#coding:utf-8
#nature@20100725

def args2py(args, sep='=', seps=[',', ';']):
    '''
    >>> args2py('port=6000 path=p1,p3 -path=p2 mode=t debug=1 flup={k1={f1=g1;f2=g2},k2=v2;v2} ab'.split())
    {'ab': None, '-path': 'p2', 'mode': 't', 'flup': {'k2': ['v2', 'v2'], 'k1': {'f1': 'g1', 'f2': 'g2'}}, 'debug': '1', 'path': ['p1', 'p3'], 'port': '6000'}
    '''
    result = {}
    for pair in args:
        index = pair.find(sep)
        if index < 0:
            result[pair] = None
        else:
            key = pair[:index]
            value = pair[index+1:]
            if not seps:
                result[key] = value
                continue
            if value.startswith('{') and value.endswith('}'):
                result[key] = line2py(value[1:-1], sep, seps)
                continue
            values = value.split(seps[0])
            if len(values) > 1:
                result[key] = values
            else:
                result[key] = value
    return result

def line2py(line, sep='=', seps=[None, ',', ';']):
    '''
    >>> line2py('port=6000 path=p1,p3 -path=p2 mode=t debug=1 flup={k1={f1=g1;f2=g2},k2=v2;v2} ab')
    {'ab': None, '-path': 'p2', 'mode': 't', 'flup': {'k2': ['v2', 'v2'], 'k1': {'f1': 'g1', 'f2': 'g2'}}, 'debug': '1', 'path': ['p1', 'p3'], 'port': '6000'}
    '''
    return args2py(line.split(seps[0]), sep, seps[1:])

def mix2py(*args):
    '''
    >>> mix2py('k1=v1', 'k2=v2,v2 k3=v3', ['k4=v4'], {'k5':'v5'})
    {'k3': 'v3', 'k2': ['v2', 'v2'], 'k1': 'v1', 'k5': 'v5', 'k4': 'v4'}
    '''
    result = {}
    for arg in args:
        if isinstance(arg, str):
            result.update(line2py(arg))
        elif isinstance(arg, dict):
            result.update(arg)
        elif isinstance(arg, list) or isinstance(arg, tuple):
            result.update(mix2py(*arg))
        else:
            raise Exception
    return result

if __name__ == '__main__':
    import doctest
    doctest.testmod()
