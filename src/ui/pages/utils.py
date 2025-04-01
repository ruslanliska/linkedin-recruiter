def proccess_search_variable(variable):
    if not variable:
        return None
    else:
        return variable.split(';')
