from starlette.datastructures import QueryParams

def validate_query_or_body(given: QueryParams, required: set):
    params = [arg for arg in given]
    if len(params) > len(required):
        return False # too many parameters supplied
    parameters = set(given)
    if not parameters.issubset(required):  # params are subset of required
        return False
    for key in given:
        if len(given.getlist(key)):
            return False
    return True