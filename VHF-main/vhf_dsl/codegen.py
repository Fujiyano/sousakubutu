"""
DSL -> Python ソースコード生成器。

`vhf_dsl/compiler.py` は DSL を **ランタイム**で `NodeTransformer` クラスに変換するが、
こちらは同等の Python **ソースコード文字列**を吐き出す。
出力を `vulnerability_handlers.py` に貼り付けると、そのまま手書きハンドラーとして
既存パイプラインに組み込める。

使い方:
    from vhf_dsl.codegen import generate_handler_source
    from vhf_dsl.lexer import tokenize
    from vhf_dsl.parser import parse

    handlers = parse(tokenize(open('rule.vhf').read()))
    src = generate_handler_source(
        handlers,
        class_name='RewriteXxx',
        register_fn_name='fix_xxx',
        source_desc='vhf_dsl/examples/print_and_eval.vhf',
    )
    print(src)
"""

from typing import List, Tuple

from .parser import Handler, FuncExpr, NameExpr, ConstExpr


def _emit_dotted_match(var: str, parts: Tuple[str, ...]) -> str:
    """`var` がドット区切り名 `parts` にマッチするかを確認する式を生成。"""
    if len(parts) == 1:
        return f"isinstance({var}, ast.Name) and {var}.id == {parts[0]!r}"
    conds = []
    cur = var
    for attr in reversed(parts[1:]):
        conds.append(f"isinstance({cur}, ast.Attribute)")
        conds.append(f"{cur}.attr == {attr!r}")
        cur = f"{cur}.value"
    conds.append(f"isinstance({cur}, ast.Name)")
    conds.append(f"{cur}.id == {parts[0]!r}")
    return " and ".join(conds)


def _emit_dotted_build(parts: Tuple[str, ...]) -> str:
    """ドット区切り名 `parts` を Name/Attribute AST として構築する式を生成。"""
    if len(parts) == 1:
        return f"ast.Name(id={parts[0]!r}, ctx=ast.Load())"
    inner = f"ast.Name(id={parts[0]!r}, ctx=ast.Load())"
    for attr in parts[1:]:
        inner = f"ast.Attribute(value={inner}, attr={attr!r}, ctx=ast.Load())"
    return inner


def _emit_call_transform(transform) -> str:
    """target が FUNC のときの transform 適用コード (Call ノードを操作)。"""
    if isinstance(transform, (FuncExpr, NameExpr)):
        build = _emit_dotted_build(transform.parts)
        # 呼び出し側 (visit_Call) が各行に 12 スペースずつインデントを付けるので
        # ここでは pre-indent しない。
        return f"node.func = {build}\nreturn node"
    if isinstance(transform, ConstExpr):
        return f"return ast.copy_location(ast.Constant(value={transform.value!r}), node)"
    raise ValueError(f"unsupported transform: {transform!r}")


def _emit_name_transform(transform) -> str:
    """target が NAME のときの transform 適用コード (Name/Attribute ノードを置換)。"""
    if isinstance(transform, (NameExpr, FuncExpr)):
        build = _emit_dotted_build(transform.parts)
        return f"return ast.copy_location({build}, node)"
    if isinstance(transform, ConstExpr):
        return f"return ast.copy_location(ast.Constant(value={transform.value!r}), node)"
    raise ValueError(f"unsupported transform: {transform!r}")


def _emit_const_transform(transform) -> str:
    """target が CONST のときの transform 適用コード。"""
    if isinstance(transform, ConstExpr):
        return f"return ast.copy_location(ast.Constant(value={transform.value!r}), node)"
    if isinstance(transform, (NameExpr, FuncExpr)):
        build = _emit_dotted_build(transform.parts)
        return f"return ast.copy_location({build}, node)"
    raise ValueError(f"unsupported transform: {transform!r}")


def generate_handler_source(
    handlers: List[Handler],
    class_name: str = "DSLCompiledTransformer",
    register_fn_name: str = "fix_dsl_compiled",
    source_desc: str = "(DSL)",
) -> str:
    """parse された handler 群から Python ソース文字列を返す。"""
    func_handlers = [h for h in handlers if h.target.kind == "FUNC"]
    name_handlers = [h for h in handlers if h.target.kind == "NAME"]
    const_handlers = [h for h in handlers if h.target.kind == "CONST"]

    lines: List[str] = []
    lines.append(f"# =====================================================================")
    lines.append(f"# === DSL-compiled handler (auto-generated from {source_desc})")
    lines.append(f"# ===   {len(handlers)} handler(s): "
                 f"FUNC={len(func_handlers)}, NAME={len(name_handlers)}, CONST={len(const_handlers)}")
    lines.append(f"# =====================================================================")
    lines.append(f"class {class_name}(ast.NodeTransformer):")

    # visit_Call (FUNC handlers)
    if func_handlers:
        lines.append("    def visit_Call(self, node):")
        lines.append("        self.generic_visit(node)")
        for i, h in enumerate(func_handlers):
            cond = _emit_dotted_match("node.func", h.target.parts)
            kw = "if" if i == 0 else "elif"
            lines.append(f"        {kw} {cond}:  # handler: {h.name}")
            body = _emit_call_transform(h.transform)
            for line in body.split("\n"):
                lines.append(f"            {line}")
        lines.append("        return node")
        lines.append("")

    # visit_Name + visit_Attribute (NAME handlers)
    single_name_handlers = [h for h in name_handlers if len(h.target.parts) == 1]
    multi_name_handlers = [h for h in name_handlers if len(h.target.parts) > 1]
    if single_name_handlers:
        lines.append("    def visit_Name(self, node):")
        lines.append("        self.generic_visit(node)")
        for i, h in enumerate(single_name_handlers):
            (ident,) = h.target.parts
            kw = "if" if i == 0 else "elif"
            lines.append(f"        {kw} node.id == {ident!r}:  # handler: {h.name}")
            body = _emit_name_transform(h.transform)
            lines.append(f"            {body}")
        lines.append("        return node")
        lines.append("")
    if multi_name_handlers:
        lines.append("    def visit_Attribute(self, node):")
        lines.append("        self.generic_visit(node)")
        for i, h in enumerate(multi_name_handlers):
            cond = _emit_dotted_match("node", h.target.parts)
            kw = "if" if i == 0 else "elif"
            lines.append(f"        {kw} {cond}:  # handler: {h.name}")
            body = _emit_name_transform(h.transform)
            lines.append(f"            {body}")
        lines.append("        return node")
        lines.append("")

    # visit_Constant (CONST handlers)
    if const_handlers:
        lines.append("    def visit_Constant(self, node):")
        for i, h in enumerate(const_handlers):
            val = h.target.value
            kw = "if" if i == 0 else "elif"
            lines.append(
                f"        {kw} node.value == {val!r} and type(node.value) is {type(val).__name__}:  "
                f"# handler: {h.name}"
            )
            body = _emit_const_transform(h.transform)
            lines.append(f"            {body}")
        lines.append("        return node")
        lines.append("")

    # 登録関数
    lines.append("")
    lines.append("@node_fixer.add")
    lines.append(f"def {register_fn_name}(ast_callbacks):")
    lines.append("    new_ast_callbacks = []")
    lines.append("    for ast_callback in ast_callbacks:")
    lines.append('        node = ast_callback.get("ast")')
    lines.append(f"        new_node = {class_name}().visit(node)")
    lines.append("        ast.fix_missing_locations(new_node)")
    lines.append("        new_ast_callbacks.append(make_new_callback(ast_callback, new_node=new_node))")
    lines.append("    return new_ast_callbacks")

    return "\n".join(lines) + "\n"
