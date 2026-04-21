#!/usr/bin/env python3

#framework object
from router import *
from request import Request
from response import Response
from inserted_functions import *

# python standard library
import ast
import inspect
import re
from wsgiref.simple_server import make_server
from wsgiref.headers import Headers
import time

class App:
    def __init__(self):
        self.router = Router()

    def route(self, path=None, method='GET'):
        def decorator(callback_func):
            self.router.add(method, path, callback_func)
            return callback_func
        return decorator

    def run(self, port=8000):
        #fix callback functions
        starting_time = time.time()
        self.router.fix()
        overhead = time.time() - starting_time
        print("starting overhead is {} sec".format(overhead))
        with make_server('', port, self) as httpd:
            print('Serving HTTP on port {}'.format(port))
            httpd.serve_forever()

    def __call__(self, env, start_response):
        request = Request(env)
        response = Response()
        # ユーザごとの動きの検出とそのためのインスタンスの探索, 作成
        ip_addr = request.client_ip_addr
        callback, status, kwargs = self.router.match(request.method, request.path)
        if callback:
            body = callback(request, **kwargs)
        else:
            body = '404 Not Found'

        response.addBody(body)
        response.makeStatusCode(status)
        #responseのためのあれ
        status_code, headers, encoded_body = response.makeResponse()
        start_response(status_code, headers)
        return encoded_body

app = App()
