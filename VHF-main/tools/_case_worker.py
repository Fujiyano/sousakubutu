"""
単一ケース実行用ワーカー。`run_dsl_cases.py` から 1 ケース 1 プロセスで呼ばれる。

- rule.vhf が存在する: register_dsl でそのケース専用のハンドラを登録して Fix.fixStatic を走らせる
- rule.vhf が存在しない: 何も登録せず Fix.fixStatic だけを走らせる
  (= 既存の手書きハンドラだけが動く。case5 用)
"""

import pathlib
import sys

# プロジェクトルートを import path に追加 (tools/ から 1 階層上)
_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from callback_fixer import Fix


def main(case_dir: str) -> None:
    case = pathlib.Path(case_dir)
    before = (case / "before.py").read_text(encoding="utf-8")

    rule = case / "rule.vhf"
    if rule.exists():
        from vhf_dsl import register_dsl
        register_dsl(rule.read_text(encoding="utf-8"), name=f"dsl_{case.name}")

    sys.stdout.write(Fix().fixStatic(before))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python _case_worker.py <case_dir>", file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1])
