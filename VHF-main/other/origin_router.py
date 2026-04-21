from callback_fixer import Fix
import re
import inspect

def http404(*args, **kwargs):
    return '404 Not Found'

def http405():
    return '405 Method Not Allowed'


class Router:
    def __init__(self):
        self.routes = []
        self.fixed_routes = []

    def add(self, method, path, callback):
        # new_callback = self.addCallbacks(callback)
        self.routes.append({
            'method': method,
            'path': path,
            'path_compiled': re.compile(path),
            'callback': callback
        })

    def match(self, method, path):
        status = '404'
        # 404 function store and return
        error_callback = http404
        for r in self.routes:
            matched = re.compile(r['path']).match(path)# 正規表現が難しい(行頭, 行末)
            if not matched:
                continue
            status = '405'
            # 405 function store and return
            error_callback = http405
            url_vars = matched.groupdict()
            if r['method'] == method:
                status = '200'
                return r['callback'], status, url_vars

        return error_callback, status, {}

    def fix(self):
        callback_fixer = Fix()
        # routesのcallbackをsourceに変換しておく？
        self.routes = callback_fixer.fix(self.routes)


def add():
    print("add_function_call")
    a = 1
    b = 3
    return 1



if __name__=="__main__":
    def add():
        print("add_function_call")
        a = 1
        b = 3
        return 1

    def sub():
        print("sub_function_call")
        a = 1
        b = 3
        return 2

    router = Router()
    router.add(method="GET", path="^/$", callback=add)
    router.add(method="POST", path="^/index$", callback=sub)
    router.match(method="GET", path="/")
    router.match(method="POST", path="/index")
