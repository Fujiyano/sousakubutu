import ast

def parse_config(s):
    parsed = ast.literal_eval(s)
    return parsed
