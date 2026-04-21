"""
vhf_dsl の動作確認用テスト。
実行 (プロジェクトルートから): py -3.13 tests/test_vhf_dsl.py
"""

import ast
import pathlib
import sys

# プロジェクトルートを import path に追加 (tests/ から 1 階層上)
_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from vhf_dsl import compile_dsl
from vhf_dsl.lexer import tokenize
from vhf_dsl.parser import parse
from vhf_dsl.compiler import compile_handlers, CompileError


def _check(label, source, dsl, expected_substr):
    Transformer = compile_dsl(dsl)
    tree = ast.parse(source)
    new_tree = Transformer().visit(tree)
    ast.fix_missing_locations(new_tree)
    out = ast.unparse(new_tree)
    ok = expected_substr in out
    status = "OK " if ok else "NG "
    print(f"[{status}] {label}")
    print(f"        input : {source.strip()}")
    print(f"        output: {out.strip()}")
    if not ok:
        print(f"        expect contains: {expected_substr!r}")
        sys.exit(1)


def test_print_to_reverse_print():
    _check(
        "print → reverse_print",
        'print("hello")',
        'handler h { target: func("print") transform: func("reverse_print") }',
        "reverse_print('hello')",
    )


def test_eval_to_none():
    _check(
        "eval → None",
        'x = eval("1+1")',
        'handler h { target: func("eval") transform: constant(None) }',
        "x = None",
    )


def test_dotted_func():
    _check(
        "ast.literal_eval → safe_eval",
        'ast.literal_eval(s)',
        'handler h { target: func("ast.literal_eval") transform: func("safe_eval") }',
        "safe_eval(s)",
    )


def test_name_replacement_does_not_touch_call_func():
    # name("print") は Call.func の print には影響しない (FUNC ハンドラと棲み分け)
    Transformer = compile_dsl(
        'handler h { target: name("user_input") transform: name("safe_user_input") }'
    )
    tree = ast.parse("query = 'SELECT ' + user_input\nprint(user_input)")
    new_tree = Transformer().visit(tree)
    ast.fix_missing_locations(new_tree)
    out = ast.unparse(new_tree)
    assert "safe_user_input" in out, out
    # Call.func の "print" は Name visitor 経由でも書き換わるが、
    # この DSL では target が user_input だけなので print は不変であることを確認
    assert "print(safe_user_input)" in out, out
    print("[OK ] name() target replaces variable refs only when name matches")
    print(f"        output: {out.strip()}")


def test_combined_handlers_in_single_traversal():
    Transformer = compile_dsl(
        """
        handler a { target: func("print")  transform: func("reverse_print") }
        handler b { target: func("eval")   transform: constant(None) }
        handler c { target: name("danger") transform: name("safe") }
        """
    )
    src = """
print("hi")
x = eval("2+2")
y = danger + 1
"""
    tree = ast.parse(src)
    new_tree = Transformer().visit(tree)
    ast.fix_missing_locations(new_tree)
    out = ast.unparse(new_tree)
    assert "reverse_print" in out and "x = None" in out and "safe + 1" in out, out
    # visit_Call / visit_Name はそれぞれ 1 つだけのはず → メソッド名で確認
    methods = {m for m in dir(Transformer) if m.startswith("visit_")}
    assert "visit_Call" in methods and "visit_Name" in methods
    print("[OK ] combined transformer applies all handlers in one traversal")
    print(f"        output: {out.strip()}")


def test_duplicate_target_is_compile_error():
    dsl = """
    handler h1 { target: func("print") transform: func("a") }
    handler h2 { target: func("print") transform: func("b") }
    """
    try:
        compile_dsl(dsl)
    except CompileError as e:
        print(f"[OK ] duplicate target rejected: {e}")
        return
    print("[NG ] duplicate target was NOT rejected")
    sys.exit(1)


def test_lexer_keywords_and_strings():
    toks = tokenize('handler x { target: func("a.b") transform: constant(None) }')
    kinds = [t.kind for t in toks]
    assert kinds == [
        "HANDLER", "IDENT", "LBRACE", "TARGET", "FUNC", "LPAREN", "STRING", "RPAREN",
        "TRANSFORM", "CONSTANT", "LPAREN", "KEYWORD", "RPAREN", "RBRACE", "EOF",
    ], kinds
    print("[OK ] lexer token sequence")


def test_example_file():
    p = _PROJECT_ROOT / "vhf_dsl" / "examples" / "print_to_reverse.vhf"
    src = p.read_text(encoding="utf-8")
    handlers = parse(tokenize(src))
    Transformer = compile_handlers(handlers)
    tree = ast.parse('print(user_input)\nx = eval("1+1")\nast.literal_eval(s)')
    new_tree = Transformer().visit(tree)
    ast.fix_missing_locations(new_tree)
    out = ast.unparse(new_tree)
    assert "reverse_print(safe_user_input)" in out, out
    assert "x = None" in out, out
    assert "safe_eval(s)" in out, out
    print("[OK ] example .vhf file loads and compiles")
    print(f"        output: {out.strip()}")


if __name__ == "__main__":
    test_lexer_keywords_and_strings()
    test_print_to_reverse_print()
    test_eval_to_none()
    test_dotted_func()
    test_name_replacement_does_not_touch_call_func()
    test_combined_handlers_in_single_traversal()
    test_duplicate_target_is_compile_error()
    test_example_file()
    print("\nall tests passed.")
