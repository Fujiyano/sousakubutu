"""
DSL を使って単一の Python ファイルを書き換えて stdout に出す簡易ツール。
使い方 (プロジェクトルートから):
    py -3.13 tools/run_dsl_on_file.py <dsl_file.vhf> <target_file.py>

例:
    py -3.13 tools/run_dsl_on_file.py vhf_dsl/examples/print_to_reverse.vhf callback_before.py
"""

import pathlib
import sys

# プロジェクトルートを import path に追加 (tools/ から 1 階層上)
_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from vhf_dsl import register_dsl
from callback_fixer import Fix


def main(dsl_path: str, src_path: str) -> None:
    dsl_text = pathlib.Path(dsl_path).read_text(encoding="utf-8")
    src_text = pathlib.Path(src_path).read_text(encoding="utf-8")
    register_dsl(dsl_text, name="cli_dsl")
    sys.stdout.write(Fix().fixStatic(src_text))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
