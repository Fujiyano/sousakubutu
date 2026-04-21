"""
VHF のハンドラー登録インフラ。
NodeFixer クラスと、ハンドラーから使う検索系ユーティリティのみを置く。
実際の脆弱性ハンドラーは vulnerability_handlers.py に記述する。
"""

from inserted_functions import *

import ast
from typing import Optional


class NodeFixer(object):
    def __init__(self):
        self.node_fix_functions = []

    def add(self, fixed_func):
        def wrapper(decorated_function):
            self.node_fix_functions.append(decorated_function)
        return wrapper(fixed_func)

    def fixNodes(self, nodes):
        for fix_func in self.node_fix_functions:
            nodes = fix_func(nodes)
        return nodes


node_fixer = NodeFixer()


### search utilities (handler 側から使うための共通ヘルパ) ###

def search_return_node_from_if_auth_func(node, auth_func_name):
    ret_node = None
    orelse_ret_node = None
    for n in ast.walk(node):
        if isinstance(n, ast.If):
            if isinstance(n.test, ast.Call) and isinstance(n.test.func, ast.Name) and n.test.func.id is auth_func_name:
                ret_node = search_ret_node(n.body)
                orelse_ret_node = search_ret_node(n.orelse)
    return ret_node, orelse_ret_node


def search_same_dump_return_nodes(node, ret_nodes):
    l = []
    for n in ast.walk(node):
        if isinstance(n, ast.Return):
            for ret_node in ret_nodes:
                if ast.dump(n) == ast.dump(ret_node):
                    l.append(n)
    return l


def search_ret_node(nodes):
    for node in nodes:
        for n in ast.walk(node):
            if isinstance(n, ast.Return):
                return n
    return None


def search_orelse_node(nodes, not_if_auth_ret_node):
    for node_dict in nodes:
        if ast.dump(node_dict['ret_node']) == ast.dump(not_if_auth_ret_node):
            return node_dict['orelse_ret_node']
    return None


def make_new_callback(callback, new_node=None):
    """ハンドラー側で書き換え後ノードを callback dict に詰め直すためのヘルパ。"""
    new_callback = {}
    if new_node:
        new_callback = {
            'callback_name': callback.get('callback_name'),
            'method': callback.get('method'),
            'path': callback.get('path'),
            'path_compiled': callback.get('path_compiled'),
            'ast': new_node
        }
        return new_callback
    return callback


### test code ###
if __name__ == "__main__":
    import inspect
    # vulnerability_handlers.py を読み込んで登録済みハンドラー一覧を表示する
    import vulnerability_handlers  # noqa: F401
    for f in node_fixer.node_fix_functions:
        print(inspect.getsource(f))
