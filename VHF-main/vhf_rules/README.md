# vhf_rules/

このディレクトリに置いた `*.vhf` ファイルは、`main.py` (または `my_server.py`) 起動時に
**自動的にコンパイル & node_fixer に登録**される。

## 流れ

```
   [*.vhf をここに置く]
            ↓
   main.py 起動
            ↓
   vhf_dsl.autoload.autoload_rules(Path("vhf_rules"))
   が全ファイルを舐める
            ↓
   各 .vhf を register_dsl() でコンパイル
            ↓
   node_fixer に @node_fixer.add 相当で登録
            ↓
   Fix().fixStatic() が走ると自動適用
```

## 置き方

- 1 ファイル 1 機能でもいいし、関連するルールをまとめて 1 ファイルにしてもよい
- ファイル名は `.vhf` 拡張子なら何でもよい (サブディレクトリは探索しない)
- コメントは `#` から行末まで

## サンプル

- [`print_and_eval.vhf`](print_and_eval.vhf) — `print` → `reverse_print`, `eval` → `None`, `ast.literal_eval` → `safe_eval`

## 注意

- 同じターゲットを別ファイルで複数回宣言するとコンパイルエラーになる
  (例: `a.vhf` にも `b.vhf` にも `func("print")` があるとアウト)
- サンプルを試したいだけなら `vhf_dsl/examples/` 側に置くこと
  (そちらは autoload の対象外)
