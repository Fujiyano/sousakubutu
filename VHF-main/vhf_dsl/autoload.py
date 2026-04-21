"""
vhf_rules/ 配下の .vhf ファイルを全部読み込んで node_fixer に登録するオートローダー。

想定フロー:
    .vhf を vhf_rules/ に配置
        ↓
    main.py (または my_server.py) 起動時に autoload_rules() を呼ぶ
        ↓
    register_dsl() が各ファイルをコンパイルして node_fixer に add
        ↓
    Fix().fixStatic() でソースコードが書き換わる

使い方:
    from vhf_dsl.autoload import autoload_rules
    autoload_rules()                         # デフォルト: プロジェクトルート/vhf_rules
    autoload_rules(Path("my_custom_rules"))  # 明示指定も可
"""

from __future__ import annotations

import pathlib
from typing import List, Optional

from .compiler import register_dsl

# このファイル (vhf_dsl/autoload.py) から見たプロジェクトルート
_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
_DEFAULT_RULES_DIR = _PROJECT_ROOT / "vhf_rules"


def autoload_rules(
    rules_dir: Optional[pathlib.Path] = None,
    verbose: bool = True,
) -> List[pathlib.Path]:
    """
    `rules_dir` 直下の *.vhf を全部読み込んで node_fixer に登録する。

    - サブディレクトリは探索しない (必要なら後で再帰化)
    - ファイル名 (拡張子除く) が DSL ハンドラーの name として使われる
    - 見つからないディレクトリは警告だけ出して空リストを返す
    - 登録に成功した .vhf のパス一覧を返す

    Args:
        rules_dir: .vhf を探すディレクトリ。None ならプロジェクトルート/vhf_rules
        verbose:   True なら登録状況を stderr に 1 行ずつ出力

    Returns:
        登録に成功した .vhf ファイルの Path リスト (ソート済み)
    """
    import sys

    target_dir = rules_dir if rules_dir is not None else _DEFAULT_RULES_DIR

    if not target_dir.exists():
        if verbose:
            print(
                f"[vhf_dsl.autoload] rules dir not found: {target_dir} (skip)",
                file=sys.stderr,
            )
        return []

    if not target_dir.is_dir():
        raise NotADirectoryError(f"not a directory: {target_dir}")

    loaded: List[pathlib.Path] = []
    for vhf_path in sorted(target_dir.glob("*.vhf")):
        try:
            source = vhf_path.read_text(encoding="utf-8")
            # name には拡張子を除いたファイル名を使う (デバッグ時の識別用)
            register_dsl(source, name=f"dsl__{vhf_path.stem}")
            loaded.append(vhf_path)
            if verbose:
                rel = _safe_relative(vhf_path)
                print(f"[vhf_dsl.autoload] loaded: {rel}", file=sys.stderr)
        except Exception as e:
            # 1 ファイルの失敗で全体を止めないが、どこで失敗したかは必ず出す
            rel = _safe_relative(vhf_path)
            print(
                f"[vhf_dsl.autoload] FAILED: {rel}: {type(e).__name__}: {e}",
                file=sys.stderr,
            )
            raise

    if verbose:
        rel_dir = _safe_relative(target_dir)
        print(
            f"[vhf_dsl.autoload] {len(loaded)} rule file(s) loaded from {rel_dir}",
            file=sys.stderr,
        )
    return loaded


def _safe_relative(path: pathlib.Path) -> str:
    """プロジェクトルートからの相対パスを返す。失敗したら絶対パス。"""
    try:
        return str(path.resolve().relative_to(_PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)
