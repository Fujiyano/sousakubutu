handler rewrite_print_to_reverse_print {
  target: func("print")
  transform: func("reverse_print")
}
