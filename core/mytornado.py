#coding:utf-8
# huangchuantong@kingsoft.com
'''
xtornado的实现代码
'''

import logging
import sys
import tornado
import urllib
import time
import gzip
import greenlet
from functools import wraps

from tornado import escape
from tornado import ioloop
from tornado.escape import utf8
from tornado.util import b
from tornado.web import ChunkedTransferEncoding, GZipContentEncoding
from cStringIO import StringIO as BytesIO  # python 2

def greenlet_fetch(url, **kwargs):
    gr = greenlet.getcurrent()
#    assert gr.parent is not None, "greenlet_fetch() can only be called (possibly indirectly) from a RequestHandler method wrapped by the greenlet_asynchronous decorator."

    def callback(response):
        gr.switch(response)

    http_client = tornado.httpclient.AsyncHTTPClient()
    http_client.fetch(url, callback, **kwargs)

    # Now, yield control back to the master greenlet, and wait for data to be sent to us.
    response = gr.parent.switch()

    return response

def greenlet_asynchronous(wrapped_method):
    """
    Decorator that allows you to make async calls as if they were synchronous
    """
    @wraps(wrapped_method)
    def wrapper(self, request):

        def greenlet_base_func():
            wrapped_method(self, request)
            request.finish()

        gr = greenlet.greenlet(greenlet_base_func)
        gr.switch()

    return wrapper

class WSGIContainer(object):
    r"""经过修改后的tornado.wsgi接口，支持非阻塞的的HTTP请求,只适用于stars

        def simple_app(environ, start_response):
            status = "200 OK"
            response_headers = [("Content-type", "text/plain")]
            start_response(status, response_headers)
            return ["Hello world!\n"]

        container = WSGIContainer(simple_app)
        http_server = tornado.httpserver.HTTPServer(container)
        http_server.listen(8888)
        tornado.ioloop.IOLoop.instance().start()

    This class is intended to let other frameworks (Django, web.py, etc)
    run on the Tornado HTTP server and I/O loop.

    The `tornado.web.FallbackHandler` class is often useful for mixing
    Tornado and WSGI apps in the same server.  See
    https://github.com/bdarnell/django-tornado-demo for a complete example.
    """
    def __init__(self, wsgi_application):
        self.wsgi_application = wsgi_application

    @greenlet_asynchronous
    def __call__(self, request):
        data = {}
        response = []

        def start_response(status, response_headers, exc_info = None):
            data["status"] = status
            data["headers"] = response_headers
            return response.append

        environ= WSGIContainer.environ(request)
        app_response = self.wsgi_application(
            environ, start_response)
        response.extend(app_response)
        body = b("").join(response)
        if hasattr(app_response, "close"):
            app_response.close()
        if not data:
            raise Exception("WSGI app did not call start_response")

        body = escape.utf8(body)
        headers = data["headers"]
        header_set = set(k.lower() for (k, v) in headers)

        if "content-length" not in header_set:
            headers.append(("Content-Length", str(len(body))))
        if "content-type" not in header_set:
            headers.append(("Content-Type", "text/html; charset=UTF-8;ext=json"))
        if "server" not in header_set:
            headers.append(("Server", "xTornado/%s" % tornado.version))

        parts = [escape.utf8("HTTP/1.1 " + data["status"] + "\r\n")]
        for key, value in headers:
            parts.append(escape.utf8(key) + b(": ") + escape.utf8(value) + b("\r\n"))
        parts.append(b("\r\n"))
        parts.append(body)
        request.write(b("").join(parts))
        # 正常流程写完数据后调用finish,这里留给greenlet装饰器调用
        # request.finish()

    @staticmethod
    def environ(request):
        """Converts a `tornado.httpserver.HTTPRequest` to a WSGI environment.
        """
        hostport = request.host.split(":")
        if len(hostport) == 2:
            host = hostport[0]
            port = int(hostport[1])
        else:
            host = request.host
            port = 443 if request.protocol == "https" else 80
        environ = {
            "REQUEST_METHOD": request.method,
            "SCRIPT_NAME": "",
            "PATH_INFO": urllib.unquote(request.path),
            "QUERY_STRING": request.query,
            "REMOTE_ADDR": request.remote_ip,
            "SERVER_NAME": host,
            "SERVER_PORT": str(port),
            "SERVER_PROTOCOL": request.version,
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": request.protocol,
            "wsgi.input": BytesIO(escape.utf8(request.body)),
            "wsgi.errors": sys.stderr,
            "wsgi.multithread": False,
            "wsgi.multiprocess": True,
            "wsgi.run_once": False,
        }
        if "Content-Type" in request.headers:
            environ["CONTENT_TYPE"] = request.headers.pop("Content-Type")
        if "Content-Length" in request.headers:
            environ["CONTENT_LENGTH"] = request.headers.pop("Content-Length")
        for key, value in request.headers.iteritems():
            environ["HTTP_" + key.replace("-", "_").upper()] = value
        return environ

    def _log(self, status_code, request):
        if status_code < 400:
            log_method = logging.info
        elif status_code < 500:
            log_method = logging.warning
        else:
            log_method = logging.error
        request_time = 1000.0 * request.request_time()
        summary = request.method + " " + request.uri + " (" + \
            request.remote_ip + ")"
        log_method("%d %s %.2fms", status_code, summary, request_time)
