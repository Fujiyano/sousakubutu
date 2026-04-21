"""
DSL Compiler.

複数の handler を 1 つの ast.NodeTransformer サブクラスに統合する。
ターゲット種別ごとに visit_Call / visit_Name / visit_Constant を生成し、
同一種別内では if/elif で分岐する。

意味論:
    target: func("x.y")     → Call ノードで、func 部分が x.y のもの
    transform: func("a.b")  → 一致した Call の func 部分を a.b に書き換える
    transform: constant(v)  → 一致した Call ノードを Constant(v) に置換する
    transform: name("a")    → 一致した Call の func 部分を Name("a") に書き換える

    target: name("v")       → Call.func 以外で出現する Name/Attribute "v"
    transform: name("w")    → Name/Attribute "w" に置換
    transform: constant(v)  → Constant(v) に置換

    target: constant(v)     → Constant(v) ノード
    transform: ...          → 同上
"""

import ast
from typing import Dict, List, Tuple

from .parser import Handler, FuncExpr, NameExpr, ConstExpr, Expr


class CompileError(Exception):
    pass


def _build_dotted(parts: Tuple[str, ...], ctx=None) -> ast.expr:
    """('foo','bar','baz') → Attribute(Attribute(Name('foo'),'bar'),'baz')"""
    if ctx is None:
        ctx = ast.Load()
    if len(parts) == 1:
        return ast.Name(id=parts[0], ctx=ctx)
    node: ast.expr = ast.Name(id=parts[0], ctx=ast.Load())
    for attr in parts[1:-1]:
        node = ast.Attribute(value=node, attr=attr, ctx=ast.Load())
    node = ast.Attribute(value=node, attr=parts[-1], ctx=ctx)
    return node


def _matches_dotted(node: ast.expr, parts: Tuple[str, ...]) -> bool:
    """node が parts 相当のドット名にマッチするか。"""
    cur = node
    chain: List[str] = []
    while isinstance(cur, ast.Attribute):
        chain.append(cur.attr)
        cur = cur.value
    if not isinstance(cur, ast.Name):
        return False
    chain.append(cur.id)
    chain.reverse()
    return tuple(chain) == parts


def _const_to_node(value) -> ast.expr:
    return ast.Constant(value=value)


def _expr_signature(expr: Expr) -> Tuple[str, object]:
    """重複検出用の正規化キー。"""
    if isinstance(expr, FuncExpr):
        return ("FUNC", expr.parts)
    if isinstance(expr, NameExpr):
        return ("NAME", expr.parts)
    if isinstance(expr, ConstExpr):
        return ("CONST", expr.value)
    raise CompileError(f"unknown expr: {expr!r}")


def _apply_transform_to_call(node: ast.Call, transform: Expr) -> ast.AST:
    if isinstance(transform, FuncExpr):
        node.func = _build_dotted(transform.parts, ctx=ast.Load())
        return node
    if isinstance(transform, NameExpr):
        node.func = _build_dotted(transform.parts, ctx=ast.Load())
        return node
    if isinstance(transform, ConstExpr):
        return _const_to_node(transform.value)
    raise CompileError(f"unsupported transform for Call: {transform!r}")


def _apply_transform_to_name(node: ast.expr, transform: Expr) -> ast.AST:
    if isinstance(transform, NameExpr):
        return _build_dotted(transform.parts, ctx=getattr(node, "ctx", ast.Load()))
    if isinstance(transform, FuncExpr):
        return _build_dotted(transform.parts, ctx=getattr(node, "ctx", ast.Load()))
    if isinstance(transform, ConstExpr):
        return _const_to_node(transform.value)
    raise CompileError(f"unsupported transform for Name: {transform!r}")


def _apply_transform_to_constant(node: ast.Constant, transform: Expr) -> ast.AST:
    if isinstance(transform, ConstExpr):
        return _const_to_node(transform.value)
    if isinstance(transform, NameExpr):
        return _build_dotted(transform.parts, ctx=ast.Load())
    if isinstance(transform, FuncExpr):
        return _build_dotted(transform.parts, ctx=ast.Load())
    raise CompileError(f"unsupported transform for Constant: {transform!r}")


def compile_handlers(handlers: List[Handler]):
    """handler 群を 1 つの NodeTransformer サブクラスに統合する。"""
    by_kind: Dict[str, List[Handler]] = {"FUNC": [], "NAME": [], "CONST": []}
    seen: Dict[Tuple[str, object], str] = {}

    for h in handlers:
        sig = _expr_signature(h.target)
        if sig in seen:
            raise CompileError(
                f"duplicate target {sig} in handler '{h.name}' (already used by '{seen[sig]}')"
            )
        seen[sig] = h.name
        by_kind[h.target.kind].append(h)

    func_handlers = by_kind["FUNC"]
    name_handlers = by_kind["NAME"]
    const_handlers = by_kind["CONST"]

    class CombinedTransformer(ast.NodeTransformer):
        # ハンドラ参照を class attribute として保持(クロージャ ID 衝突回避)
        _func_handlers = list(func_handlers)
        _name_handlers = list(name_handlers)
        _const_handlers = list(const_handlers)

        def visit_Call(self, node: ast.Call):
            self.generic_visit(node)
            for h in self._func_handlers:
                target = h.target
                assert isinstance(target, FuncExpr)
                if _matches_dotted(node.func, target.parts):
                    new_node = _apply_transform_to_call(node, h.transform)
                    return ast.copy_location(new_node, node)
            return node

        def visit_Name(self, node: ast.Name):
            self.generic_visit(node)
            for h in self._name_handlers:
                target = h.target
                assert isinstance(target, NameExpr)
                if len(target.parts) == 1 and node.id == target.parts[0]:
                    new_node = _apply_transform_to_name(node, h.transform)
                    return ast.copy_location(new_node, node)
            return node

        def visit_Attribute(self, node: ast.Attribute):
            self.generic_visit(node)
            for h in self._name_handlers:
                target = h.target
                assert isinstance(target, NameExpr)
                if len(target.parts) > 1 and _matches_dotted(node, target.parts):
                    new_node = _apply_transform_to_name(node, h.transform)
                    return ast.copy_location(new_node, node)
            return node

        def visit_Constant(self, node: ast.Constant):
            for h in self._const_handlers:
                target = h.target
                assert isinstance(target, ConstExpr)
                if node.value == target.value and type(node.value) is type(target.value):
                    new_node = _apply_transform_to_constant(node, h.transform)
                    return ast.copy_location(new_node, node)
            return node

    CombinedTransformer.__name__ = "CombinedDSLTransformer"
    return CombinedTransformer


def build_node_fixer_callback(handlers: List[Handler]):
    """node_fixer.add に渡せる callback を作って返す。"""
    Transformer = compile_handlers(handlers)

    def make_new_callback(callback, new_node):
        return {
            "callback_name": callback.get("callback_name"),
            "method": callback.get("method"),
            "path": callback.get("path"),
            "path_compiled": callback.get("path_compiled"),
            "ast": new_node,
        }

    def dsl_fixer(ast_callbacks):
        new_ast_callbacks = []
        for ast_callback in ast_callbacks:
            node = ast_callback.get("ast")
            new_node = Transformer().visit(node)
            ast.fix_missing_locations(new_node)
            new_ast_callbacks.append(make_new_callback(ast_callback, new_node=new_node))
        return new_ast_callbacks

    return dsl_fixer


def register_dsl(source: str, name: str = "dsl_handlers"):
    """DSL ソースをパース・コンパイルし node_fixer に登録する。"""
    from .lexer import tokenize
    from .parser import parse

    handlers = parse(tokenize(source))
    callback = build_node_fixer_callback(handlers)
    callback.__name__ = name

    from node_fixer import node_fixer

    node_fixer.add(callback)
    return callback
