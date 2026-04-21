# print / eval / ast.literal_eval を一気に書き換える DSL ルール。
# tools/gen_handler_from_dsl.py でこのファイルから Python コードを
# 生成して vulnerability_handlers.py に追記する。

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
