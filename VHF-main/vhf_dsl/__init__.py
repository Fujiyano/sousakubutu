"""
VHF DSL: 脆弱性書き換えパターンを宣言的に記述するためのミニ言語。

公開 API:
    compile_dsl(source: str) -> type[ast.NodeTransformer]
    register_dsl(source: str, name: str = "dsl_handlers") -> None
        node_fixer に統合済みのコールバックを add する。
"""

from .lexer import tokenize
from .parser import parse
from .compiler import compile_handlers, build_node_fixer_callback, register_dsl
from .autoload import autoload_rules

__all__ = [
    "tokenize",
    "parse",
    "compile_handlers",
    "build_node_fixer_callback",
    "register_dsl",
    "compile_dsl",
    "autoload_rules",
]


def compile_dsl(source: str):
    """DSL ソース → 統合 NodeTransformer クラスを返す。"""
    handlers = parse(tokenize(source))
    return compile_handlers(handlers)
