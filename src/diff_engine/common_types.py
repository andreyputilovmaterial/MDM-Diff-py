

from collections import deque # for find_common_format





class ErrorInlineMarkupNotSupported(Exception):
    """ ... """
class ErrorDiffClassesNotPossibleToDetect(Exception):
    """ Each returned segment must clearly identify if it's a "change" segment or "context" segment; if it does not, and did_change() is invoke, we fail """
def detect_str_block_type(input):
    # if '<<ADDED>>' in input or '<<REMOVED>>' in input:
    #     raise ErrorInlineMarkupNotSupported(f'Error: found <<ADDED>> or <<REMOVED>> marker in string; this is not supported anymore')
    raise ErrorDiffClassesNotPossibleToDetect(f'Each returned segment must clearly identify if it\'s a "change" segment or "context" segment: {input} of type {detect_format(input)}') # should be already detected at this point - we can't detect if it's input or a change block from string; it should have been wrapped with dict with { "role" : ...}
def detect_block_type(input):
    if is_empty(input):
        return 'blank'
    input_fmt = detect_format(input)
    if isinstance(input,dict):
        role = input.get('role',None)
        if role in ('added','removed'):
            return 'change'
        elif role in ('context',):
            return 'context'
        elif 'parts' in input and isinstance(input['parts'],list):
            return detect_block_type(input['parts'])
        elif 'text' in input:
            return detect_block_type(input['text'])
        else:
            raise ErrorDiffClassesNotPossibleToDetect(f'Each returned segment must clearly identify if it\'s a "change" segment or "context" segment: {input} of type {detect_format(input)}')
    elif input_fmt == '(none)':
        return None
    elif input_fmt == '(propertylist)':
        context_found = False
        change_found = False
        for row in input:
            piece = row['value']
            piece_type = detect_block_type(piece)
            change_found = change_found or piece_type == 'change'
            context_found = context_found or piece_type == 'context'
            assert (piece_type in ('change','context','blank',)) or (piece_type is None and is_empty(piece)), 'Failed: each piece should be ChangeBlock or ContextBlock, or be empty'
        return 'change' if change_found else 'context'
    elif input_fmt == '(list)':
        context_found = False
        change_found = False
        for piece in input:
            piece_type = detect_block_type(piece)
            change_found = change_found or piece_type == 'change'
            context_found = context_found or piece_type == 'context'
            assert (piece_type in ('change','context','blank',)) or (piece_type is None and is_empty(piece)), 'Failed: each piece should be ChangeBlock or ContextBlock, or be empty'
        return 'change' if change_found else 'context'
    elif input_fmt == '(str)':
        return detect_str_block_type(input)
    raise ErrorDiffClassesNotPossibleToDetect(f'Each returned segment must clearly identify if it\'s a "change" segment or "context" segment: {input} of type {detect_format(input)}')

def filter_diff_input_from_diff_classes(input):
    input_fmt = detect_format(input)
    if isinstance(input,dict):
        role = input.get('role',None)
        result = {**input}
        if role in ('added','removed'):
            # roles_prev = input.get('roles_prev',[])
            # roles_prev.append(role)
            # result['role'] = None
            # result['roles_prev'] = roles_prev
            result['role'] = f'underlying_{result["role"]}'
        # if 'parts' in input and detect_format(input['parts']) in ['(list)','(propertylist)']:
        if 'parts' in input:
            result['parts'] =  filter_diff_input_from_diff_classes(result['parts'])
        if 'text' in input:
            result['text'] =  filter_diff_input_from_diff_classes(result['text'])
        if 'text' not in result and 'parts' not in result:
            raise Exception(f'Can\' filter prev inputs and clean from prev diff classes: {input} of type {input_fmt}')
        return result
    elif input_fmt == '(none)':
        return input
    elif input_fmt == '(propertylist)':
        return [ { 'name': piece['name'], 'value': filter_diff_input_from_diff_classes(piece['value']) } for piece in input ]
    elif input_fmt == '(list)':
        return [ filter_diff_input_from_diff_classes(piece) for piece in input ]
    elif input_fmt == '(str)':
        return input
    raise Exception(f'Can\' filter prev inputs and clean from prev diff classes: {input} of type {input_fmt}')


def as_segment_context(input):
    return {'role':'context','text':input}

def as_segment_change(input,op):
    assert op in ('added','removed',), f'Change segment must be of "added" or "removed" op, got "{op}" ({input})'
    return {'role':op,'text':input}

def did_change(input):
    return detect_block_type(input) == 'change'

# class HunkSegmentMixin:
#     def detect_format(self):
#         return detect_format(self)
#     def did_change(self):
#         return detect_block_type(self) == 'change'

# class ChangeSegmentMixin(HunkSegmentMixin):
#     def det_type(self):
#         return 'change'

# class ChangeSegmentStr(ChangeSegmentMixin,str):
#     def detect_format(self):
#         return '(str)'

# class ChangeSegmentList(ChangeSegmentMixin,list):
#     def detect_format(self):
#         return '(propertylist)'

# class ChangeSegmentPropertylist(ChangeSegmentMixin,list):
#     def detect_format(self):
#         return '(list)'

# class ChangeSegmentDict(ChangeSegmentMixin,dict):
#     def detect_format(self):
#         return '(dict)'






# class ContextSegmentMixin(HunkSegmentMixin):
#     def det_type(self):
#         return 'context'

# class ContextSegmentStr(ContextSegmentMixin,str):
#     def detect_format(self):
#         return '(str)'

# class ContextSegmentList(ContextSegmentMixin,list):
#     def detect_format(self):
#         return '(list)'

# class ContextSegmentPropertylist(ContextSegmentMixin,list):
#     def detect_format(self):
#         return '(propertylist)'

# class ContextSegmentDict(ContextSegmentMixin,dict):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#     def detect_format(self):
#         return '(dict)'

# class ContextSegment(ContextSegmentDict):
#     def __init__(self,value):
#         if isinstance(value,dict):
#             super().__init__(**value)
#         else:
#             super().__init__(text=value)
#         self.deep_update_roles()
#     def deep_update_roles(self):
#         if 'role' in self and self['role']:
#             pass

    




def is_empty(s):
    if s==0:
        return False
    elif isinstance(s,dict):
        if not s:
            return True
        if 'text' in s and not is_empty(s['text']):
            return False
        if 'parts' in s and not is_empty(s['parts']):
            return False
        return True
    elif is_property_list(s):
        if not s:
            return True
        result = True
        for piece in s:
            result = result and is_empty(piece['value'])
        return result
    elif isinstance(s,list):
        if not s:
            return True
        result = True
        for piece in s:
            result = result and is_empty(piece)
        return result
    else:
        # attention
        # empty list, empty dict evaluates to empty
        return not s


def is_property_list(data):
    try:
        if isinstance(data,list) and ([(True if ('name' in dict.keys(item) and 'value' in dict.keys(item)) else False) for item in data].count(True)==len(data)):
            return True
        return False
    except:
        return False

def detect_format(val,avoid_none=False):
    if not avoid_none and is_empty(val):
        return '(none)'
    elif isinstance(val,list) and len(val)==0:
        return '(none)'
    elif is_property_list(val):
        return '(propertylist)'
    elif isinstance(val,list):
        return '(list)'
    elif isinstance(val,dict):
        return '(dict)'
    elif isinstance(val,str):
        return '(str)'
    elif is_empty(val):
        return '(none)'
    else:
        return '(uncategorized)'

def as_format_none(inp,source_fmt=None):
    if is_empty(inp):
        return None
    else:
        raise Exception(f'Can\'t convert to (none): {inp}')

def as_format_uncategorized(inp,source_fmt=None):
    return inp

def as_format_str(inp,source_fmt=None):
    if is_empty(inp):
        return ''
    else:
        return f'{inp}'

def as_format_propertylist(inp,source_fmt=None):
    if source_fmt in ['(list)']:
        return [ { 'name': f'_{i}', 'value': val } for i,val in enumerate(inp) ]
    else:
        return as_format_propertylist(as_format_list(inp,source_fmt),source_fmt='(list)')

def as_format_list(inp,source_fmt=None):
    if source_fmt in ['(propertylist)','(list)']:
        return inp
    else:
        if is_empty(inp):
            return []
        else:
            return [inp]

def as_format_dict(inp,source_fmt=None):
    if source_fmt in ['(propertylist)','(list)']:
        return {'parts':inp}
    else:
        return {'text':inp}

possible_transformations = {
        '(sysmissing)': {},
        '(none)': {
            '(propertylist)' : as_format_propertylist,
            '(list)': as_format_list,
            '(dict)': as_format_dict,
            '(str)': as_format_str,
        },
        '(uncategorized)': {
            '(str)': as_format_str,
        },

        '(str)': {
            '(propertylist)': as_format_propertylist,
            '(list)': as_format_list,
            '(dict)': as_format_dict,
        },
        '(list)': {
            '(dict)': as_format_dict,
            '(uncategorized)': as_format_uncategorized,
        },
        '(propertylist)': {
            '(list)': as_format_list,
            '(uncategorized)': as_format_uncategorized,
        },
        '(dict)': {
            '(uncategorized)': as_format_uncategorized,
        },
    }

def as_format(inp, format_source, format_dest):
    if format_source==format_dest:
        return inp
    converter = possible_transformations.get(format_source,{}).get(format_dest,None)
    if not converter:
        raise Exception(f'Hmmm, reading compared values for diff, called to convert format from {format_source} to {format_dest} but converter fn is not found')
    result = converter(inp,format_source)
    # assert detect_format(result) in [format_dest,'(none)','(uncategorized)'], f'Hmmm, reading compared values for diff, called to convert format from {format_source} to {format_dest}, successfully converted but the target format does not match the dest ({detect_format(result)})'
    return result

class CommonFormatNotFound(Exception):
    """Raised when common of 2 formats is not found, and should be caught"""
    pass
def find_common_format_denominator(sig1, sig2):

    def reachable_with_distance(start):
        distances = {start: 0}
        queue = deque([start])

        steps_secure_no_inifinite_loop = 0
        while queue:
            steps_secure_no_inifinite_loop += 1
            if steps_secure_no_inifinite_loop>100:
                raise CommonFormatNotFound(f'Common of {sig1} and {sig2} not found. Can\'t find derived format that is common for both input signatiures (step overflow)')
            node = queue.popleft()
            for nxt in possible_transformations.get(node, {}):
                if nxt not in distances:
                    distances[nxt] = distances[node] + 1
                    queue.append(nxt)

        return distances


    def closest_common(a, b):
        da = reachable_with_distance(a)
        db = reachable_with_distance(b)

        common = set(da) & set(db)

        if not common:
            raise CommonFormatNotFound(f'Common of {a} and {b} not found. Can\'t find derived format that is common for both input signatiures')

        return min(common, key=lambda x: da[x] + db[x])

    return closest_common(sig1,sig2)
    # return tuple(closest_common(spec1,spec2) for spec1,spec2 in zip(sig1,sig2))

def find_common_format_denominator_with_fallback_str(*args):
    try:
        return find_common_format_denominator(*args)
    except CommonFormatNotFound:
        return '(str)'

