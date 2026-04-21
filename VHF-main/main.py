#callback_lists.pyに配置されたコールバック関数にVHFを適用する関数
#収集したコールバック関数の中には実行できないプログラム(import先のモジュールがない等)が混じっているので文字列にしてVHFを適用
#実行の例:python main.py callback_before.py --out callback_after.py

from __future__ import annotations

from pathlib import Path
import difflib

# DSL ルール (vhf_rules/*.vhf) を node_fixer に自動登録する。
# 必ず callback_fixer.Fix を import する前後どちらでもよいが、
# 「DSL ファイルを置くだけで適用される」流れを表現するため先に呼ぶ。
from vhf_dsl import autoload_rules
autoload_rules()

from callback_fixer import Fix

INPUT_FILE = Path.home() / "VHF-main" / "callback_before.py"          # 入力（VHF適用前）
OUTPUT_FILE = Path.home() / "VHF-main" / "callback_after" / "after.py"   # 修正後を保存したいなら（Noneなら保存しない）
SHOW_FIXED_CODE = False            # Trueにすると修正後コードも全文表示


def unified_diff(original: str, fixed: str, from_name: str, to_name: str) -> str:
    return "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            fixed.splitlines(keepends=True),
            fromfile=from_name,
            tofile=to_name,
        )
    )


def main() -> None:
    in_path = Path(INPUT_FILE)
    if not in_path.exists():
        raise FileNotFoundError(f"Input file not found: {in_path.resolve()}")

    original = in_path.read_text(encoding="utf-8")

    fixer = Fix()
    fixed = fixer.fixStatic(original)

    diff_text = unified_diff(original, fixed, str(in_path), str(in_path) + " (fixed)")
    print(diff_text if diff_text else "[diff] no changes")

    if OUTPUT_FILE is not None:
        out_path = Path(OUTPUT_FILE)
        out_path.write_text(fixed, encoding="utf-8")
        print(f"[saved] {out_path.resolve()}")

    if SHOW_FIXED_CODE:
        print("\n===== [FIXED CODE] =====")
        print(fixed)


if __name__ == "__main__":
    main()
###