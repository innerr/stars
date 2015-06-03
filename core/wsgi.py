#coding:utf-8
#
# Author: CMGS
# Created on 2011-3-4
#

def tornado(entry, app, port, params):
    import tornado.wsgi
    import tornado.httpserver
    import tornado.ioloop

    try:
        container = tornado.wsgi.WSGIContainer(Application(app, entry))
        server = tornado.httpserver.HTTPServer(container)
        server.listen(port = port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        pass
    print 'Closing...'

def xtornado(entry, app, port, params):
    import mytornado
    import tornado.httpserver
    import tornado.ioloop

    try:
        container = mytornado.WSGIContainer(Application(app, entry))
        server = tornado.httpserver.HTTPServer(container)
        server.listen(port = port)
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        pass
    print 'Closing...'

def bjoern(entry, app, port, params):
    import bjoern
    def server(environ, start_response):
        headers, response = entry(environ, app)
        start_response('200 OK', headers)
        if isinstance(response, str):
            response = (response,)
        return response
    try:
        bjoern.listen(server, '0.0.0.0', port)
        bjoern.run()
    except KeyboardInterrupt:
        pass
    print 'Closing...'

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
