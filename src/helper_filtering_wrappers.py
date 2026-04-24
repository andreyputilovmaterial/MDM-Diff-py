
import re


if __name__ == '__main__':
    # run as a program
    import helper_diff_wrappers
elif '.' in __name__:
    # package
    from . import helper_diff_wrappers
else:
    # included with no parent package
    import helper_diff_wrappers




def clean_role_underlying_dict(o):
    assert isinstance(o,dict), f'clean_role_underlying_dict: must be a dict ({o})'
    if 'role' in o and o['role']:
        role = o.get('role',None)
        if role in ['added','removed']:
            o['role'] = None
            o['role_underlying'] = role
        elif role in ['ellipsis']:
            o['text'] = ' <... ...> '
        else:
            pass
    return o

def clean_role_underlying_deep(data):
    if isinstance(data,str):
        # TODO: drop support of <<ADDED>>, <<REMOVED>> markers
        if '<<ADDED>>' in data or '<<REMOVED>>' in data:
            return re.replace('<<ADDED>>','<<ADDED-KEEP>>').replace('<<REMOVED>>','<<REMOVED-KEEP>>').replace('<<ENDADDED>>','<<ENDADDED-KEEP>>').replace('<<ENDREMOVED>>','<<ENDREMOVED-KEEP>>')
        return data
    elif isinstance(data,list):
        result = []
        for slice in data:
            result += [clean_role_underlying_deep(slice)]
        return result
    elif isinstance(data,dict):
        data = clean_role_underlying_dict(data)
        result = {
            key: clean_role_underlying_deep(value) for key, value in data.items()
        }
        return result
    elif helper_diff_wrappers.is_empty(data):
        return data
    else:
        return data
        # return clean_role_underlying_deep(f'{data}')






def check_if_includes_addedremoved_marker(data):
    if helper_diff_wrappers.is_empty(data):
        return False
    elif helper_diff_wrappers.is_property_list(data):
        # property list
        result = False
        for prop in data:
            result = result or check_if_includes_addedremoved_marker(prop['value'])
        return result
    elif isinstance(data,list):
        # just list of somethigng
        result = False
        for e in data:
            result = result or check_if_includes_addedremoved_marker(e)
        return result
    elif isinstance(data,dict) and ('role' in dict.keys(data)) and data['role'] and re.match(r'^\s*?(?:role-)?(add|remove|change).*?$',f"{data['role']}",flags=re.I):
        return True
    elif isinstance(data,dict) and ('parts' in dict.keys(data)):
        return check_if_includes_addedremoved_marker(data['parts'])
    elif isinstance(data,dict) and 'text' in dict.keys(data):
        return check_if_includes_addedremoved_marker(data['text'])
    elif isinstance(data,str):
        # TODO: drop support of <<ADDED>>, <<REMOVED>> markers
        if ('<<ADDED>>' in '{fmt}'.format(fmt=data)) or ('<<REMOVED>>' in '{fmt}'.format(fmt=data)):
            return True
        return False
    elif isinstance(data,dict) or isinstance(data,list):
        # raise ValueError('Can\'t handle this type of data: {d}'.format(d=data))
        #return check_if_includes_addedremoved_marker(json.dumps(data))
        return check_if_includes_addedremoved_marker('{d}'.format(d=data))
    elif (f'{data}'==data):
        # TODO: drop support of <<ADDED>>, <<REMOVED>> markers
        if ('<<ADDED>>' in '{fmt}'.format(fmt=data)) or ('<<REMOVED>>' in f'{data}'):
            return True
        return False
    else:
        # raise ValueError('Can\'t handle this type of data: {d}'.format(d=data))
        #return check_if_includes_addedremoved_marker(json.dumps(data))
        return check_if_includes_addedremoved_marker(f'{data}')




def did_contents_change_deep_inspect(data):
    if isinstance(data,str):
        # TODO: drop support of <<ADDED>>, <<REMOVED>> markers
        if '<<ADDED>>' in data:
            return True
        if '<<REMOVED>>' in data:
            return True
        return False
    elif helper_diff_wrappers.is_property_list(data):
        result = False
        for slice in data:
            result = result or did_contents_change_deep_inspect(slice['value'])
        return result
    elif isinstance(data,list):
        result = False
        for slice in data:
            result = result or did_contents_change_deep_inspect(slice)
        return result
    elif isinstance(data,dict) and 'text' in data:
        if 'role' in data and data['role']:
            role = data['role']
            if isinstance(role,str):
                if re.match(r'^\s*?(?:role-)?(?:added|removed).*?',role,flags=re.I):
                    return True
            else:
                print(f'WARNING: role is not str ({role})')
        return did_contents_change_deep_inspect(data['text'])
    elif isinstance(data,dict) and 'parts' in data:
        return did_contents_change_deep_inspect(data['parts'])
    elif isinstance(data,dict) and 'name' in data and 'value' in data:
        return did_contents_change_deep_inspect(data['value'])
    else:
        return did_contents_change_deep_inspect(f'{data}')

