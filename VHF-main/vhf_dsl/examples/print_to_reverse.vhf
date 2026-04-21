# 例1: print → reverse_print
handler rewrite_print_to_reverse_print {
  target: func("print")
  transform: func("reverse_print")
}

# 例2: eval を None に置換 (削除)
handler remove_eval {
  target: func("eval")
  transform: constant(None)
}

# 例3: ドット区切り — ast.literal_eval → safe_eval
handler rewrite_literal_eval {
  target: func("ast.literal_eval")
  transform: func("safe_eval")
}

# 例4: 変数参照 user_input → safe_user_input (SQLi 用途想定)
handler wrap_user_input {
  target: name("user_input")
  transform: name("safe_user_input")
}
