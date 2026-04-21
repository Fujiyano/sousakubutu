"""
DSL Lexer.

トークン種別:
    HANDLER   'handler'
    TARGET    'target:'
    TRANSFORM 'transform:'
    FUNC      'func'
    NAME      'name'
    CONSTANT  'constant'
    LBRACE    '{'
    RBRACE    '}'
    LPAREN    '('
    RPAREN    ')'
    STRING    "..." または '...'
    NUMBER    数値リテラル
    KEYWORD   None / True / False
    IDENT     識別子
    EOF
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Token:
    kind: str
    value: object
    line: int
    col: int

    def __repr__(self) -> str:
        return f"Token({self.kind}, {self.value!r}, L{self.line}:C{self.col})"


class LexError(Exception):
    pass


KEYWORDS = {
    "handler": "HANDLER",
    "func": "FUNC",
    "name": "NAME",
    "constant": "CONSTANT",
    "None": "KEYWORD",
    "True": "KEYWORD",
    "False": "KEYWORD",
}

SINGLE_CHAR = {
    "{": "LBRACE",
    "}": "RBRACE",
    "(": "LPAREN",
    ")": "RPAREN",
    ",": "COMMA",
}


def tokenize(source: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    line = 1
    col = 1
    n = len(source)

    while i < n:
        c = source[i]

        if c == "\n":
            line += 1
            col = 1
            i += 1
            continue
        if c in " \t\r":
            i += 1
            col += 1
            continue
        if c == "#":
            while i < n and source[i] != "\n":
                i += 1
            continue

        if c in SINGLE_CHAR:
            tokens.append(Token(SINGLE_CHAR[c], c, line, col))
            i += 1
            col += 1
            continue

        if c in ('"', "'"):
            quote = c
            start_line, start_col = line, col
            i += 1
            col += 1
            buf = []
            while i < n and source[i] != quote:
                if source[i] == "\\" and i + 1 < n:
                    nxt = source[i + 1]
                    esc = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", quote: quote}.get(nxt, nxt)
                    buf.append(esc)
                    i += 2
                    col += 2
                    continue
                if source[i] == "\n":
                    raise LexError(f"unterminated string at L{start_line}:C{start_col}")
                buf.append(source[i])
                i += 1
                col += 1
            if i >= n:
                raise LexError(f"unterminated string at L{start_line}:C{start_col}")
            i += 1
            col += 1
            tokens.append(Token("STRING", "".join(buf), start_line, start_col))
            continue

        if c.isdigit() or (c == "-" and i + 1 < n and source[i + 1].isdigit()):
            start_col = col
            j = i + 1
            seen_dot = False
            while j < n and (source[j].isdigit() or (source[j] == "." and not seen_dot)):
                if source[j] == ".":
                    seen_dot = True
                j += 1
            text = source[i:j]
            value = float(text) if seen_dot else int(text)
            tokens.append(Token("NUMBER", value, line, start_col))
            col += j - i
            i = j
            continue

        if c.isalpha() or c == "_":
            start_col = col
            j = i + 1
            while j < n and (source[j].isalnum() or source[j] == "_"):
                j += 1
            word = source[i:j]

            # 'target:' / 'transform:' は ':' まで含めて判定
            if j < n and source[j] == ":" and word in ("target", "transform"):
                kind = "TARGET" if word == "target" else "TRANSFORM"
                tokens.append(Token(kind, word, line, start_col))
                col += (j - i) + 1
                i = j + 1
                continue

            kind = KEYWORDS.get(word, "IDENT")
            value: object = word
            if kind == "KEYWORD":
                value = {"None": None, "True": True, "False": False}[word]
            tokens.append(Token(kind, value, line, start_col))
            col += j - i
            i = j
            continue

        raise LexError(f"unexpected character {c!r} at L{line}:C{col}")

    tokens.append(Token("EOF", None, line, col))
    return tokens
