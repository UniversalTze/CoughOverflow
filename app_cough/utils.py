from starlette.datastructures import QueryParams

def validate_query(given: QueryParams, required: set):
    params = [arg for arg in given]
    if len(params) > len(required):
        return False # too many parameters supplied
    parameters = set(params)
    if not parameters.issubset(required):  # params are subset of required
        return False
    for key in given:
        if len(given.getlist(key)) > 1:
            return False
    return True

def validate_body(args: list, required: set):
    if len(args) != len(required):
        return False # too many parameters supplied (should only be one)
    for item in args: 
        if item != 'image':
            return False
    return True