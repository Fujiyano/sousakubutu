"""
dsl_demo_cases/ 配下の各ケースを 1 ケース 1 プロセスで独立実行し、
before/after/DSL を並べて表示する。

- 各ケースごとに subprocess を起動 → node_fixer のハンドラ登録が他ケースに漏れない
- 環境: py -3.13 推奨

使い方 (プロジェクトルートから):
    py -3.13 tools/run_dsl_cases.py
"""

import pathlib
import subprocess
import sys

# Windows の既定コンソール (cp932) でも壊れないよう stdout を UTF-8 に再構成
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
CASES_DIR = ROOT / "dsl_demo_cases"
WORKER = HERE / "_case_worker.py"


def _banner(text: str, char: str = "=") -> str:
    return f"{char * 4} {text} {char * max(4, 70 - len(text) - 6)}"


def run_case(case_dir: pathlib.Path) -> bool:
    before = (case_dir / "before.py").read_text(encoding="utf-8")
    rule_path = case_dir / "rule.vhf"

    print(_banner(case_dir.name, "="))

    if rule_path.exists():
        print(_banner("rule.vhf", "-"))
        print(rule_path.read_text(encoding="utf-8").rstrip())
    else:
        print(_banner("rule.vhf", "-"))
        print("(no DSL rule - existing hand-written handlers only)")

    print(_banner("before.py", "-"))
    print(before.rstrip())

    print(_banner("after (stdout)", "-"))
    result = subprocess.run(
        [sys.executable, str(WORKER), str(case_dir)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        print(f"!! worker failed with code {result.returncode}")
        print(result.stderr)
        return False
    print(result.stdout.rstrip())
    if result.stderr.strip():
        print(_banner("worker stderr", "-"))
        print(result.stderr.rstrip())
    print()
    return True


def main() -> int:
    cases = sorted(p for p in CASES_DIR.iterdir() if p.is_dir())
    if not cases:
        print(f"no cases under {CASES_DIR}", file=sys.stderr)
        return 2

    all_ok = True
    for case in cases:
        ok = run_case(case)
        all_ok = all_ok and ok

    print(_banner(f"{len(cases)} cases done", "="))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
