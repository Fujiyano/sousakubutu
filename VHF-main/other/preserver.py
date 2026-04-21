from app import *

# @app.route("パスの正規表現",  "リクエストメソッド")
# def コールバック関数(request):
#   コールバック関数内の処理
#   return "webブラウザに返却するページ"


def _get_param(request, key, default=""):
    # Try multiple common request APIs.
    try:
        if hasattr(request, "args") and hasattr(request.args, "get"):
            return request.args.get(key, default)
        if hasattr(request, "query") and hasattr(request.query, "get"):
            return request.query.get(key, default)
        if hasattr(request, "params") and hasattr(request.params, "get"):
            return request.params.get(key, default)
    except Exception:
        pass
    return default

"""
CWE-94 (Code Injection) - Vulnerable (direct eval from user input)
"""
@app.route("^/testcase1$", "GET")
def testcase1(request):
    expr = _get_param(request, "expr", "")
    # DANGEROUS: direct eval of untrusted input
    try:
        result = eval(expr)
    except Exception as e:
        return f"error: {e}"
    return f"Result: {result}"


if __name__=="__main__":
  app.run(port=8000)