# このフォルダ (vhf_rules/) に置いた .vhf は main.py 起動時に
# 自動コンパイル & node_fixer 登録される。
#
# 書き方の詳細: ../DSL_USAGE.md
# サンプル集:   ../vhf_dsl/examples/

handler rewrite_print_to_reverse_print {
  target:    func("print")
  transform: func("reverse_print")
}

handler remove_eval {
  target:    func("eval")
  transform: constant(None)
}

handler rewrite_literal_eval {
  target:    func("ast.literal_eval")
  transform: func("safe_eval")
}
