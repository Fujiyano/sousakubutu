"""
.vhf DSL から Python の脆弱性ハンドラー (NodeTransformer + 登録関数) を生成する CLI。

使い方 (プロジェクトルートから):

    # 1) 生成してターミナルに出力するだけ
    py -3.13 tools/gen_handler_from_dsl.py <rule.vhf> <ClassName> <fn_name>

    # 2) 生成して vulnerability_handlers.py に追記する
    py -3.13 tools/gen_handler_from_dsl.py <rule.vhf> <ClassName> <fn_name> --append

例:
    py -3.13 tools/gen_handler_from_dsl.py \\
        vhf_dsl/examples/print_and_eval.vhf \\
        RewritePrintAndEval \\
        fix_print_and_eval \\
        --append

追記は冪等 (idempotent): 生成されるブロックの先頭に
「=== DSL-compiled handler (auto-generated from <path>) ===」コメントがあり、
同じ source_desc のブロックが既にあるなら追記をスキップする。
"""

import pathlib
import sys

# プロジェクトルートを import path に追加
_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from vhf_dsl.codegen import generate_handler_source
from vhf_dsl.lexer import tokenize
from vhf_dsl.parser import parse


TARGET_FILE = _PROJECT_ROOT / "vulnerability_handlers.py"
MARKER_PREFIX = "# === DSL-compiled handler (auto-generated from "


def main() -> int:
    args = sys.argv[1:]
    if len(args) < 3:
        print(__doc__, file=sys.stderr)
        return 2

    rule_path_str, class_name, fn_name, *rest = args
    append = "--append" in rest

    rule_path = pathlib.Path(rule_path_str)
    if not rule_path.exists():
        print(f"rule file not found: {rule_path}", file=sys.stderr)
        return 2

    dsl_src = rule_path.read_text(encoding="utf-8")
    handlers = parse(tokenize(dsl_src))
    # 表示用は相対パス (プロジェクトルートからの相対)
    try:
        source_desc = str(rule_path.resolve().relative_to(_PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        source_desc = str(rule_path)

    generated = generate_handler_source(
        handlers=handlers,
        class_name=class_name,
        register_fn_name=fn_name,
        source_desc=source_desc,
    )

    if not append:
        sys.stdout.write(generated)
        return 0

    # --append: 冪等に追記
    existing = TARGET_FILE.read_text(encoding="utf-8")
    marker_line = f"{MARKER_PREFIX}{source_desc})"
    if marker_line in existing:
        print(
            f"[skip] vulnerability_handlers.py に既に {source_desc!r} の生成ブロックがあります",
            file=sys.stderr,
        )
        return 0

    # 末尾に改行 + 生成コードを追記
    separator = "\n\n" if not existing.endswith("\n\n") else ""
    TARGET_FILE.write_text(existing + separator + generated, encoding="utf-8")
    print(
        f"[ok] {source_desc} -> vulnerability_handlers.py に {class_name} を追記",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
