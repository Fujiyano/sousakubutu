handler rewrite_literal_eval {
  target: func("ast.literal_eval")
  transform: func("safe_eval")
}
