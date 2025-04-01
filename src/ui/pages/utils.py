def proccess_search_variable(variable):
    if not variable:
        return None
    else:
        return [var.strip() for var in variable.split(';')]
