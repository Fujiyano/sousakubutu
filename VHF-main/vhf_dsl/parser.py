"""
DSL Parser.

文法 (EBNF):
    program   = handler+ ;
    handler   = 'handler' IDENT '{' 'target:' expr 'transform:' expr '}' ;
    expr      = funcExpr | nameExpr | constExpr ;
    funcExpr  = 'func' '(' STRING ')' ;
    nameExpr  = 'name' '(' STRING ')' ;
    constExpr = 'constant' '(' value ')' ;
    value     = STRING | NUMBER | 'None' | 'True' | 'False' ;

ターゲット種別:
    FUNC: Call ノード (func 部分のドット区切り名で識別)
    NAME: Name / Attribute ノード (Call.func 以外の参照)
    CONST: Constant ノード
"""

from dataclasses import dataclass
from typing import List, Tuple, Union

from .lexer import Token


class ParseError(Exception):
    pass


@dataclass
class FuncExpr:
    """func("foo.bar") → Call の func がドット区切り名 'foo.bar' のものにマッチ / それを構築。"""
    parts: Tuple[str, ...]

    @property
    def kind(self) -> str:
        return "FUNC"


@dataclass
class NameExpr:
    """name("user_input") → Name(または Attribute チェーン) ノード。Call.func 以外を対象。"""
    parts: Tuple[str, ...]

    @property
    def kind(self) -> str:
        return "NAME"


@dataclass
class ConstExpr:
    """constant(value) → Constant ノード。"""
    value: object

    @property
    def kind(self) -> str:
        return "CONST"


Expr = Union[FuncExpr, NameExpr, ConstExpr]


@dataclass
class Handler:
    name: str
    target: Expr
    transform: Expr
    line: int


class _Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset: int = 0) -> Token:
        return self.tokens[self.pos + offset]

    def eat(self, kind: str) -> Token:
        tok = self.tokens[self.pos]
        if tok.kind != kind:
            raise ParseError(
                f"expected {kind} at L{tok.line}:C{tok.col}, got {tok.kind} ({tok.value!r})"
            )
        self.pos += 1
        return tok

    def parse_program(self) -> List[Handler]:
        handlers: List[Handler] = []
        while self.peek().kind != "EOF":
            handlers.append(self.parse_handler())
        return handlers

    def parse_handler(self) -> Handler:
        h_tok = self.eat("HANDLER")
        ident = self.eat("IDENT")
        self.eat("LBRACE")
        self.eat("TARGET")
        target = self.parse_expr()
        self.eat("TRANSFORM")
        transform = self.parse_expr()
        self.eat("RBRACE")
        return Handler(name=str(ident.value), target=target, transform=transform, line=h_tok.line)

    def parse_expr(self) -> Expr:
        tok = self.peek()
        if tok.kind == "FUNC":
            self.pos += 1
            self.eat("LPAREN")
            s = self.eat("STRING")
            self.eat("RPAREN")
            return FuncExpr(parts=tuple(str(s.value).split(".")))
        if tok.kind == "NAME":
            self.pos += 1
            self.eat("LPAREN")
            s = self.eat("STRING")
            self.eat("RPAREN")
            return NameExpr(parts=tuple(str(s.value).split(".")))
        if tok.kind == "CONSTANT":
            self.pos += 1
            self.eat("LPAREN")
            value = self.parse_value()
            self.eat("RPAREN")
            return ConstExpr(value=value)
        raise ParseError(
            f"expected func/name/constant at L{tok.line}:C{tok.col}, got {tok.kind}"
        )

    def parse_value(self):
        tok = self.peek()
        if tok.kind == "STRING":
            self.pos += 1
            return tok.value
        if tok.kind == "NUMBER":
            self.pos += 1
            return tok.value
        if tok.kind == "KEYWORD":
            self.pos += 1
            return tok.value
        raise ParseError(
            f"expected value at L{tok.line}:C{tok.col}, got {tok.kind}"
        )


def parse(tokens: List[Token]) -> List[Handler]:
    return _Parser(tokens).parse_program()
