#元のVHFからの変更点
#1.Fixクラス内にfixStatic関数を追加
#fixStatic関数は文字列から文字列への変換

from node_fixer import node_fixer
# 脆弱性ハンドラーを読み込んで node_fixer に登録させる
# (import するだけで @node_fixer.add の副作用で登録が走る)
import vulnerability_handlers  # noqa: F401
from inserted_functions import *

import ast
import inspect
import copy

class Fix(object):
    def __init__(self):
        self.fixed_routes = []
        self.node_fixer = node_fixer

    def fix(self, routes):
        asts = self.codeToASTs(routes)
        fixed_asts = node_fixer.fixNodes(asts)
        fixed_routes = []
        # for exec
        for fixed_ast in fixed_asts:
            node = fixed_ast.get('ast')
            callback_name = fixed_ast.get('callback_name')
            exec(compile(ast.fix_missing_locations(node), filename="<ast>", mode="exec"))
            fixed_callback = locals().get(callback_name)
            fixed_route = ({
                'method':fixed_ast.get('method'),
                'path': fixed_ast.get('path'),
                'path_compiled': fixed_ast.get('path_compiled'),
                'callback': fixed_callback
            })
            fixed_routes.append(fixed_route)
        return fixed_routes

    def codeToASTs(self, routes):
        asts = []
        for route in routes:
            callback_name = route.get('callback').__name__
            source = inspect.getsource(route.get('callback'))
            source = self.fixIndent(source)
            source = self.removeRouteDecorator(source)
            node = ast.parse(source)
            asts.append({
                'callback_name': callback_name,
                'method': route.get('method'),
                'path': route.get('path'),
                'path_compiled': route.get('path_compiled'),
                'ast': node
            })
        return asts

    def fixIndent(self, source):
        indent = 0
        fixed_source = ''
        lines = source.splitlines()
        for num in range(len(lines)):
            if num == 0 and lines[0][0] == ' ':
                for character in lines[0]:
                    if character == ' ':
                        indent += 1
                    else:
                        break
            fixed_source += lines[num].replace(' '*indent, '', 1)
            fixed_source += '\n'
        return fixed_source

    def removeRouteDecorator(self,source):
        lines = source.splitlines()
        fixed_source = ""
        for index in range(len(lines)):
            if lines[index].startswith("@"):
                break
        if len(lines) == index + 1:
            return source

        for i in range(index+1, len(lines)):
            fixed_source += lines[i] + "\n"
        return fixed_source
    


    def fixStatic(self, source: str) -> str:
        source = self.fixIndent(source)
        source = self.removeRouteDecorator(source)
        node = ast.parse(source)

        asts = [{
            "callback_name": None,
            "method": None,
            "path": None,
            "path_compiled": None,
            "ast": node
        }]
        fixed_asts = node_fixer.fixNodes(asts)
        fixed_node = fixed_asts[0]["ast"]
        ast.fix_missing_locations(fixed_node)
        return ast.unparse(fixed_node)
