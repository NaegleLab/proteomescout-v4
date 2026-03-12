def get_field_as_int(request, field_name, default):
    field_val = get(request, field_name, default)
    try:
        field_val = int(field_val)
    except:
        field_val = default
    return field_val

def get(request, var, default):
    return __check_array(request.GET, var, default)
    
def post(request, var, default):
    return __check_array(request.POST, var, default)
    
def __check_array(array, var, default):
    try:
        val = array[var]
        return val
    except KeyError:
        pass
     
    return default


def call_catch(etype, errors, method, *args, **kwargs):
    try:
        return method(*args, **kwargs)
    except etype as e:
        errors.append(e)

def object_to_dict(exp):
    expd = {}
    
    for key in exp.__dict__:
        if key[0] != "_":
            expd[key] = exp.__dict__[key]
    
    return expd
