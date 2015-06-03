#coding:utf-8
#nature@20100802

def run(entry, app, port, params, isPrefork):
    if isPrefork:
        from flup.server.fcgi_fork import WSGIServer
    else:
        from flup.server.fcgi import WSGIServer

    class Application:
        def __init__(self, app, entry):
            self._app = app
            self._entry = entry
        def __call__(self, environ, start_response):
            headers, response = self._entry(environ, self._app)
            start_response('200 OK', headers)
            if isinstance(response, str):
                response = (response,)
            return response

    for k, v in params.iteritems():
        try:
            params[k] = int(v)
        except:
            pass

    params['application'] =  Application(app, entry)
    params['bindAddress'] = ('', port)

    try:
        WSGIServer(**params).run() 
    except KeyboardInterrupt:
        pass
    print 'Closing...'
