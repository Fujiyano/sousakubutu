from callback_fixer import Fix
import re
import inspect
import difflib

def http404(*args, **kwargs):
    return '404 Not Found'

def http405():
    return '405 Method Not Allowed'


class Router:
    def __init__(self):
        self.routes = []
        self.fixed_routes = []          # 修正後ルートを保持
        self.original_routes = []       # 修正前ルートを保持（表示用）

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
            matched = re.compile(r['path']).match(path)  # 正規表現が難しい(行頭, 行末)
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

    def fix(self, show=False, show_diff=True):
        callback_fixer = Fix()

        self.original_routes = [r.copy() for r in self.routes]

        fixed = callback_fixer.fix(self.routes)
        self.fixed_routes = fixed
        self.routes = fixed

        if show:
            self.show_fixed_callbacks(show_diff=show_diff)

    def show_fixed_callbacks(self, show_diff=True):
        """
        Router.fix() 実行後を前提に、
        各ルートの callback の修正前後のコードと diff を表示する。
        """
        if not self.original_routes or not self.fixed_routes:
            print("[!] original_routes / fixed_routes が空です。先に fix() を呼んでください。")
            return

        for orig, fixed in zip(self.original_routes, self.fixed_routes):
            orig_cb = orig['callback']
            fixed_cb = fixed['callback']

            # --- 元のコールバックのソース取得 ---
            try:
                orig_src = inspect.getsource(orig_cb)
            except Exception as e:
                orig_src = (
                    f"# [ORIGINAL] ソースコード取得に失敗しました "
                    f"({type(e).__name__}: {e})\n"
                    f"# object = {orig_cb!r}"
                )

            # --- 修正後コールバックのソース取得 ---
            try:
                fixed_src = inspect.getsource(fixed_cb)
            except Exception as e:
                fixed_src = (
                    f"# [FIXED] ソースコード取得に失敗しました "
                    f"({type(e).__name__}: {e})\n"
                    f"# object = {fixed_cb!r}"
                )

            print("=" * 80)
            print(f"PATH: {orig['path']}  METHOD: {orig['method']}")
            print("----- [ORIGINAL CALLBACK] ------------------------")
            print(orig_src.rstrip(), "\n")
            print("----- [FIXED CALLBACK] ---------------------------")
            print(fixed_src.rstrip(), "\n")

            # 両方とも「ちゃんとソースが取れた」場合だけ diff を出す
            if show_diff and not orig_src.startswith("# [ORIGINAL] ソースコード取得に失敗") \
                         and not fixed_src.startswith("# [FIXED] ソースコード取得に失敗"):
                print("----- [UNIFIED DIFF] ----------------------------")
                diff = difflib.unified_diff(
                    orig_src.splitlines(keepends=True),
                    fixed_src.splitlines(keepends=True),
                    fromfile="original",
                    tofile="fixed",
                )
                print("".join(diff))
"""
if __name__ == "__main__":
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
    router.add(method="GET", path="^/$",      callback=add)
    router.add(method="POST", path="^/index$", callback=sub)

    router.fix(show=True, show_diff=True)

    router.match(method="GET", path="/")
    router.match(method="POST", path="/index")
"""