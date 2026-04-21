def build_query(user_input):
    query = "SELECT * FROM users WHERE name = '" + user_input + "'"
    log = user_input
    return query, log
