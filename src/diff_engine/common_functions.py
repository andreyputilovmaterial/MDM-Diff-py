

from collections import deque # for find_common_format
import re
from typing import ClassVar, Callable, Any





def text_split_words(s):
    """Splits continuous text into pieces, separated with "word boundaries" """
    class Splitter:
        def __init__(self,data):
            self.data = data
            self.delimiter = r"(?:\w*?_|\w+|\s+|.)"
            
        def __iter__(self):
            delimiters = re.finditer(self.delimiter,self.data,flags=re.M|re.DOTALL|re.I)
            delimiters = [ delim.start(0) for delim in delimiters ]
            parts = []
            start = 0
            for delim in delimiters:
                pos = delim
                parts.append(self.data[start:pos])
                start = pos
            parts.append(self.data[start:])
            return iter(parts)
    return [a for a in Splitter(s)]

def sanitize_text_normalizelinebreaks(inp_value):
    assert isinstance(inp_value,str), f'sanitize_text_normalizelinebreaks: input must be str, got {inp_value}'
    result =  re.sub(r'\r','\n',re.sub(r'\r\n',' \n',inp_value))
    assert len(result) == len(inp_value), 'sanitize_text_normalizelinebreaks: str length must be preserved!'
    return result

def text_split_lines(s):
    """Splits continuous text into pieces, separated with newline characters"""
    return sanitize_text_normalizelinebreaks(f'{s}').split("\n")





class ErrorDiffClassesNotPossibleToDetect(Exception):
    """Raised when segment type can't be detected
    
    "Segments" are specific type of output diff is producing.
    It is basically a dict with "role" indicating segment role
    
    "Role" indicates its type - if it's an "change" block (with something added/removed), or "context" that is not reported
    as actual result, but is still needed to show where the change block is located

    This is only important when we call diff on diffs. So we need to filter inputs and identify "segment types" first. If something
    is a "change" block - we process it. If something is "context" - we pass through. If else - not sure, that's where we catch this exception and see what we can do/should do
    """
def detect_diffsegment_str_role(input: str):
    """A function to detect segment type, specifically if input is str
    Basically, segment type can not be indicating in string. It should always be endicated earlier, at something that wraps strings. So, this function always fails.
    
    "Segments" are specific type of output diff is producing.
    It is basically a dict with "role" indicating segment role
    
    "Role" indicates its type - if it's an "change" block (with something added/removed), or "context" that is not reported
    as actual result, but is still needed to show where the change block is located

    This is only important when we call diff on diffs. So we need to filter inputs and identify "segment types" first. If something
    is a "change" block - we process it. If something is "context" - we pass through. If else - not sure, we'll raise and exception and handle it and see what we can do/should do
    """
    # if '<<ADDED>>' in input or '<<REMOVED>>' in input:
    #     raise ErrorInlineMarkupNotSupported(f'Error: found <<ADDED>> or <<REMOVED>> marker in string; this is not supported anymore')
    raise ErrorDiffClassesNotPossibleToDetect(f'Each returned segment must clearly identify if it\'s a "change" segment or "context" segment: {input} of type {detect_format(input)}') # should be already detected at this point - we can't detect if it's input or a change block from string; it should have been wrapped with dict with { "role" : ...}
def detect_diffsegment_role(input):
    """A function to detect segment type
    
    "Segments" are specific type of output diff is producing.
    It is basically a dict with "role" indicating segment role
    
    "Role" indicates its type - if it's an "change" block (with something added/removed), or "context" that is not reported
    as actual result, but is still needed to show where the change block is located

    This is only important when we call diff on diffs. So we need to filter inputs and identify "segment types" first. If something
    is a "change" block - we process it. If something is "context" - we pass through. If else - not sure, we'll raise and exception and handle it and see what we can do/should do
    """
    if is_empty(input):
        return None
    input_fmt = detect_format(input)
    if is_diff_segment_dict(input):
        role = input.get('role',None)
        if role in ('added','removed','source_added','source_removed','source_change',):
            return 'change'
        elif role in ('context',):
            return 'context'
        return detect_diffsegment_role(get_segment_payload(input))
    elif isinstance(input,dict):
        raise ErrorDiffClassesNotPossibleToDetect(f'Each returned segment must clearly identify if it\'s a "change" segment or "context" segment: {input} of type {detect_format(input)}')
    elif input_fmt == '(none)':
        return None
    elif input_fmt == '(propertylist)':
        context_found = False
        change_found = False
        for row in input:
            piece = row['value']
            piece_type = detect_diffsegment_role(piece)
            change_found = change_found or piece_type == 'change'
            context_found = context_found or piece_type == 'context'
            assert (piece_type in ('change','context',None,)) or (piece_type is None and is_empty(piece)), 'Failed: each piece should be ChangeBlock or ContextBlock, or be empty'
        return 'change' if change_found else 'context'
    elif input_fmt == '(list)':
        context_found = False
        change_found = False
        for piece in input:
            piece_type = detect_diffsegment_role(piece)
            change_found = change_found or piece_type == 'change'
            context_found = context_found or piece_type == 'context'
            assert (piece_type in ('change','context',None,)) or (piece_type is None and is_empty(piece)), 'Failed: each piece should be ChangeBlock or ContextBlock, or be empty'
        return 'change' if change_found else 'context'
    elif input_fmt == '(str)':
        return detect_diffsegment_str_role(input)
    raise ErrorDiffClassesNotPossibleToDetect(f'Each returned segment must clearly identify if it\'s a "change" segment or "context" segment: {input} of type {detect_format(input)}')

def detect_segment_role(input):
    if is_empty(input):
        return None
    input_fmt = detect_format(input)
    if is_diff_segment_dict(input):
        role = input.get('role',None)
        if role in ('added','removed','source_added','source_removed','source_change',):
            return 'change'
        return detect_segment_role(get_segment_payload(input)) or role
    elif isinstance(input,dict):
        result = []
        for key, value in input.items():
            role = detect_segment_role(value)
            if not is_empty(role):
                result.append()
        result = set(result)
        if len(result)==1:
            return next(iter(result))
        elif 'change' in result:
            return 'change'
        elif len(result)>1:
            # raise Exception(f'Can\'t detect role: a dict with multiple roles')
            return 'mixed'
        else:
            return None
    elif input_fmt == '(none)':
        return None
    elif input_fmt == '(propertylist)':
        result = []
        for row in input:
            piece = row['value']
            role = detect_segment_role(piece)
            result.append(role)
        result = set(result)
        if len(result)==1:
            return next(iter(result))
        elif 'change' in result:
            return 'change'
        elif len(result)>1:
            # raise Exception(f'Can\'t detect role: a list with multiple roles')
            return 'mixed'
        else:
            return None
    elif input_fmt == '(list)':
        result = []
        for piece in input:
            role = detect_segment_role(piece)
            result.append(role)
        result = set(result)
        if len(result)==1:
            return next(iter(result))
        elif 'change' in result:
            return 'change'
        elif len(result)>1:
            # raise Exception(f'Can\'t detect role: a list with multiple roles')
            return 'mixed'
        else:
            return None
    elif input_fmt == '(str)':
        return None
    return None







def normalize_input_relocate_diff_markers(input):
    """A function to filter/clean/sanitize inputs, for processing in diffing
    It checks what type of segments is found in inputs, and if it shows results
    from underlying diffs.
    
    This is only important when calling diffs on diffs, then diff classes are escaped (relocated to another property)
    
    "Segments" are specific type of output diff is producing.
    It is basically a dict with "role" indicating segment role
    
    "Role" indicates its type - if it's an "change" block (with something added/removed), or "context" that is not reported
    as actual result, but is still needed to show where the change block is located
    """
    input_fmt = detect_format(input)
    if is_diff_segment_dict(input):
        role = input.get('role',None)
        result = {**input}
        if role in ('added','removed','source_added','source_removed','source_change',):
            # roles_prev = input.get('roles_prev',[])
            # roles_prev.append(role)
            # result['role'] = None
            # result['roles_prev'] = roles_prev
            result['role'] = f'source_{result["role"]}'
        if 'parts' in input:
            result['parts'] =  normalize_input_relocate_diff_markers(get_segment_payload(result))
        if 'text' in input:
            result['text'] =  normalize_input_relocate_diff_markers(get_segment_payload(result))
        if 'text' not in result and 'parts' not in result:
            raise Exception(f'Can\' filter prev inputs and clean from prev diff classes: {input} of type {input_fmt}')
        return result
    if isinstance(input,dict):
        result = {}
        for key, value in input.items():
            result[key] = normalize_input_relocate_diff_markers(value)
        return result
    elif input_fmt == '(none)':
        return input
    elif input_fmt == '(propertylist)':
        return [ { 'name': piece['name'], 'value': normalize_input_relocate_diff_markers(piece['value']) } for piece in input ]
    elif input_fmt == '(list)':
        return [ normalize_input_relocate_diff_markers(piece) for piece in input ]
    elif input_fmt == '(str)':
        return input
    raise Exception(f'Can\' filter prev inputs and clean from prev diff classes: {input} of type {input_fmt}')


def as_segment_context(input):
    """Wraps input to dict with "role" indicating segment type (context here)
    
    "Segments" are specific type of output diff is producing.
    It is basically a dict with "role" indicating segment role
    
    "Role" indicates its type - if it's an "change" block (with something added/removed), or "context" that is not reported
    as actual result, but is still needed to show where the change block is located
    """
    return {'role':'context','text':input} if not is_segment_context(input) else input

def as_segment_change(input,op):
    """Wraps input to dict with "role" indicating segment type (change block here)
    
    "Segments" are specific type of output diff is producing.
    It is basically a dict with "role" indicating segment role
    
    "Role" indicates its type - if it's an "change" block (with something added/removed), or "context" that is not reported
    as actual result, but is still needed to show where the change block is located
    """
    assert op in ('added','removed',), f'Change segment must be of "added" or "removed" op, got "{op}" ({input})'
    if is_empty(input):
        input_fmt = detect_format(input)
        return as_format(None,input_fmt,'(segment)')
    return {'role':op,'text':input}

def did_change(input):
    """Responds to question: does anything here indicate added or removed piece, somewhere here or deeper inside"""
    return detect_diffsegment_role(input) == 'change'





def is_empty(input):
    """Responds to question if there is any content inside

    Mostly same as simply "not not input", but does not trigger zero as empty/missing value.
    Cause zero is content, while empty string, or empty dict, or "None", are not."""
    if input==0:
        return False
    elif is_diff_segment_dict(input):
        return is_empty(get_segment_payload(input))
    elif isinstance(input,dict):
        return not input
    elif is_property_list(input):
        if not input:
            return True
        result = True
        for piece in input:
            result = result and is_empty(piece['value'])
        return result
    elif isinstance(input,list):
        if not input:
            return True
        result = True
        for piece in input:
            result = result and is_empty(piece)
        return result
    else:
        # attention
        # empty list, empty dict evaluates to empty
        return not input


def is_property_list(input):
    """Helps to detect input data type, if it represents a property list - that is handled differently than just normal list"""
    try:
        if isinstance(input,list) and ([(True if ('name' in dict.keys(item) and 'value' in dict.keys(item)) else False) for item in input].count(True)==len(input)):
            return True
        return False
    except:
        return False

def is_diff_segment_dict(input):
    """Helps to detect if input represents "segment"

    "Segments" are specific type of output diff is producing.
    It is basically a dict with "role" indicating segment role
    
    "Role" indicates its type - if it's an "change" block (with something added/removed), or "context" that is not reported
    as actual result, but is still needed to show where the change block is located

    This is only important when we call diff on diffs. This way we can capture if inputs contain something significant ("change block"), or just "context"
    """
    if isinstance(input,dict):
        has_payload_textfield = 'text' in input
        has_payload_partsfield = 'parts' in input and isinstance(input['parts'],list)
        has_payload = has_payload_textfield or has_payload_partsfield
        has_conflicting_payloads = has_payload_textfield and has_payload_partsfield
        all_keys = input.keys()
        nonstd_keys = set(all_keys) - {'text','parts','role'}
        if has_payload and not has_conflicting_payloads and (len(nonstd_keys)==0):
            return True
    return False

def is_segment_context(input):
    """Helps to detect if input represents "segment" and this segment is of "context" type
    
    "Segments" are specific type of output diff is producing.
    It is basically a dict with "role" indicating segment role
    
    "Role" indicates its type - if it's an "change" block (with something added/removed), or "context" that is not reported
    as actual result, but is still needed to show where the change block is located

    This is only important when we call diff on diffs. This way we can capture if inputs contain something significant ("change block"), or just "context"
    """
    try:
        return detect_diffsegment_role(input)=='context'
    except:
        return False

def get_segment_payload(input: dict):
    assert isinstance(input,dict), f'get_segment_payload: input must be a dict'
    has_payload_textfield = 'text' in input
    has_payload_partsfield = 'parts' in input and isinstance(input['parts'],list)
    if has_payload_textfield and not has_payload_partsfield:
        return input['text']
    elif not has_payload_textfield and has_payload_partsfield:
        return input['parts']
    else:
        assert False, f'get_segment_payload: format validation failed'


def detect_format(input,avoid_none=False):
    """Main function to detect input type
    
    All diffing funcitons here work differently based on input data format - if we comapre strings, or dicts, or lists...
    So, this returns the format, out of several known values.
    This is also used to detect the format of both inputs, left and right, and find the closest common one, and bring both inputs to same format
    """
    if not avoid_none and is_empty(input):
        return '(none)'
    elif input is None:
        return '(none)'
    elif isinstance(input,list) and len(input)==0:
        return '(none)'
    elif is_property_list(input):
        return '(propertylist)'
    elif isinstance(input,list):
        return '(list)'
    elif is_diff_segment_dict(input):
        return '(segment)'
    elif isinstance(input,dict):
        return '(dict)'
    elif isinstance(input,str) or isinstance(input,(int,float,bool,)):
        return '(str)'
    elif is_empty(input):
        return '(none)'
    else:
        return '(uncategorized)'

def as_format_none(input,source_fmt=None):
    """Convert source input to format "(none)"
    
    All diffing funcitons here work differently based on input data format - if we comapre strings, or dicts, or lists...
    So, this is a part of umbrella of functions to detect and convert formats
    """
    if is_empty(input):
        return None
    else:
        raise Exception(f'Can\'t convert to (none): {input}')

def as_format_uncategorized(input,source_fmt=None):
    """Convert source input to format "(uncategorized)"
    
    All diffing funcitons here work differently based on input data format - if we comapre strings, or dicts, or lists...
    So, this is a part of umbrella of functions to detect and convert formats
    """
    return input

def as_format_str(input,source_fmt=None):
    """Convert source input to format "(str)"
    
    All diffing funcitons here work differently based on input data format - if we comapre strings, or dicts, or lists...
    So, this is a part of umbrella of functions to detect and convert formats
    """
    if is_empty(input):
        return ''
    else:
        return f'{input}'

def as_format_propertylist(input,source_fmt=None):
    """Convert source input to format "(propertylist)"
    
    All diffing funcitons here work differently based on input data format - if we comapre strings, or dicts, or lists...
    So, this is a part of umbrella of functions to detect and convert formats
    """
    if source_fmt in ['(list)']:
        return [ { 'name': f'_{i}', 'value': val } for i,val in enumerate(input) ]
    else:
        return as_format_propertylist(as_format_list(input,source_fmt),source_fmt='(list)')

def as_format_list(input,source_fmt=None):
    """Convert source input to format "(list)"
    
    All diffing funcitons here work differently based on input data format - if we comapre strings, or dicts, or lists...
    So, this is a part of umbrella of functions to detect and convert formats
    """
    if source_fmt in ['(propertylist)','(list)']:
        return input
    else:
        if is_empty(input):
            return []
        else:
            return [input]

def as_format_dict(input,source_fmt=None):
    """Convert source input to format "(dict)"
    
    All diffing funcitons here work differently based on input data format - if we comapre strings, or dicts, or lists...
    So, this is a part of umbrella of functions to detect and convert formats
    """
    if is_empty(input):
        return {}
    else:
        raise Exception(f'Can\'t convert to dict: {input}')

def as_format_segment(input,source_fmt=None):
    """Convert source input to format "(segment)"
    
    All diffing funcitons here work differently based on input data format - if we comapre strings, or dicts, or lists...
    So, this is a part of umbrella of functions to detect and convert formats
    
    "Segments" are specific type of output diff is producing.
    It is basically a dict with "role" indicating segment role
    
    "Role" indicates its type - if it's an "change" block (with something added/removed), or "context" that is not reported
    as actual result, but is still needed to show where the change block is located
    """
    if source_fmt in ['(propertylist)','(list)']:
        return {'parts':input}
    else:
        return {'text':input}

possible_transformations = {
        '(sysmissing)': {},
        '(none)': {
            '(propertylist)' : as_format_propertylist,
            '(list)': as_format_list,
            '(dict)': as_format_dict,
            '(segment)': as_format_segment,
            '(str)': as_format_str,
        },
        '(uncategorized)': {
            '(str)': as_format_str,
        },

        '(str)': {
            '(propertylist)': as_format_propertylist,
            '(list)': as_format_list,
            '(segment)': as_format_segment,
        },
        '(list)': {
            '(segment)': as_format_segment,
            '(uncategorized)': as_format_uncategorized,
        },
        '(propertylist)': {
            '(list)': as_format_list,
            '(uncategorized)': as_format_uncategorized,
        },
        '(segment)': {
            '(uncategorized)': as_format_uncategorized,
        },
        '(dict)': {
            '(uncategorized)': as_format_uncategorized,
        },
    }

def as_format(inp, format_source, format_dest):
    """Convert source input to dest format
    
    All diffing funcitons here work differently based on input data format - if we comapre strings, or dicts, or lists...
    So, this is a part of umbrella of functions to detect and convert formats
    """
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
    """Finds the closest common format of given 2
    
    All diffing funcitons here work differently based on input data format - if we comapre strings, or dicts, or lists...
    So, this is a part of umbrella of functions to detect and convert formats
    """

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
    """Finds the closest common format of given to, with fallback to "(str)"
    
    All diffing funcitons here work differently based on input data format - if we comapre strings, or dicts, or lists...
    So, this is a part of umbrella of functions to detect and convert formats
    """
    try:
        return find_common_format_denominator(*args)
    except CommonFormatNotFound:
        return '(str)'



def as_plain_text(inp_value,flags=[]):
    """Takes any possible structure taken as input, and renders it as plain text.
    Something simiar to element.textContent in html
    """
    def is_property_list(input):
        try:
            if isinstance(input,list) and ([(True if ('name' in dict.keys(item) and 'value' in dict.keys(item)) else False) for item in input].count(True)==len(input)):
                return True
            return False
        except:
            return False
    def is_diff_segment_dict(input):
        if isinstance(input,dict):
            has_payload_textfield = 'text' in input
            has_payload_partsfield = 'parts' in input and isinstance(input['parts'],list)
            has_payload = has_payload_textfield or has_payload_partsfield
            has_conflicting_payloads = has_payload_textfield and has_payload_partsfield
            all_keys = input.keys()
            nonstd_keys = set(all_keys) - {'text','parts','role'}
            if has_payload and not has_conflicting_payloads and (len(nonstd_keys)==0):
                return True
        return False
    def is_empty(input):
        if input==0:
            return False
        elif is_diff_segment_dict(input):
            return is_empty(get_segment_payload(input))
        elif isinstance(input,dict):
            return not input
        elif is_property_list(input):
            if not input:
                return True
            result = True
            for piece in input:
                result = result and is_empty(piece['value'])
            return result
        elif isinstance(input,list):
            if not input:
                return True
            result = True
            for piece in input:
                result = result and is_empty(piece)
            return result
        else:
            # attention
            # empty list, empty dict evaluates to empty
            return not input
    if is_empty(inp_value):
        return ''
    elif is_property_list(inp_value):
        def esc(s):
            return f'{s}'.replace('"','""')
        return '[ '+', '.join([f'{record["name"]} = "{esc(record["value"])}"' for record in inp_value])+' ]'
    elif is_diff_segment_dict(inp_value):
        return as_plain_text(get_segment_payload(inp_value))
    elif isinstance(inp_value,list):
        return ''.join([as_plain_text(s) for s in inp_value])
    else:
        return f'{inp_value}'

def as_sequence_with_roles(inp_value,parent_level_role=None,flags=[]):
    """Takes any possible structure taken as input, and renders it as sequence of 2-tupes[role,payload].
    Something simiar to as_plain_text but with also attached role information
    """
    def is_property_list(input):
        try:
            if isinstance(input,list) and ([(True if ('name' in dict.keys(item) and 'value' in dict.keys(item)) else False) for item in input].count(True)==len(input)):
                return True
            return False
        except:
            return False
    def is_diff_segment_dict(input):
        if isinstance(input,dict):
            has_payload_textfield = 'text' in input
            has_payload_partsfield = 'parts' in input and isinstance(input['parts'],list)
            has_payload = has_payload_textfield or has_payload_partsfield
            has_conflicting_payloads = has_payload_textfield and has_payload_partsfield
            all_keys = input.keys()
            nonstd_keys = set(all_keys) - {'text','parts','role'}
            if has_payload and not has_conflicting_payloads and (len(nonstd_keys)==0):
                return True
        return False
    def is_empty(input):
        if input==0:
            return False
        elif is_diff_segment_dict(input):
            return is_empty(get_segment_payload(input))
        elif isinstance(input,dict):
            return not input
        elif is_property_list(input):
            if not input:
                return True
            result = True
            for piece in input:
                result = result and is_empty(piece['value'])
            return result
        elif isinstance(input,list):
            if not input:
                return True
            result = True
            for piece in input:
                result = result and is_empty(piece)
            return result
        else:
            # attention
            # empty list, empty dict evaluates to empty
            return not input
    if is_empty(inp_value):
        return []
    elif is_property_list(inp_value):
        result = []
        result += [(parent_level_role,'['),(parent_level_role,' '),]
        for i,record in enumerate():
            if i>0:
                result += [(parent_level_role,','),(parent_level_role,' '),]
            txt = f'{record["name"]} = "'
            result += [(parent_level_role,char) for char in txt ]
            for letter in as_sequence_with_roles(record['value'],parent_level_role,flags):
                if letter[1]=='"':
                    result += [letter,letter] # escaping quotes
                else:
                    result += [letter]
            txt = f'"'
            result += [(parent_level_role,char) for char in txt ]
        result += [(parent_level_role,' '),(parent_level_role,']'),]
        return result
    elif is_diff_segment_dict(inp_value):
        return as_sequence_with_roles(get_segment_payload(inp_value),detect_segment_role(inp_value) or parent_level_role,flags)
    elif isinstance(inp_value,list):
        result = []
        for part in inp_value:
            result += as_sequence_with_roles(part,detect_segment_role(inp_value) or parent_level_role,flags)
        return result
    else:
        return [(parent_level_role,char) for char in f'{inp_value}' ]

def as_hash(input):
    "Takes input, and generates a hashable tuple, that consists of 1. segment type, 2. text content, rendered all as plain text without roles or formatting"
    value = as_plain_text(input)
    role = detect_segment_role(input)
    return (role,value)


def count_linebreaks(input):
    """Counts how many lines there will be when this piece is rendered as plain text, without any roles or formatting"""
    # return 0
    return len(text_split_lines(as_plain_text(input)))

def fill_same_number_linebreaks(left,right):
    """Appends necessary number of line breaks to either left or right input, so that they maatch in number of lines they occupy"""
    # TODO: eliminate the use of this, this is expensive and slow
    len_left = count_linebreaks(left)
    len_right = count_linebreaks(right)
    len_common = len_left if len_left > len_right else len_right
    add_left = len_common - len_left
    add_right = len_common - len_right
    result_left = ( [ left, as_segment_context('\n'*add_left) ] if not (detect_format(left)=='(list)') else left + [ as_segment_context('\n'*add_left) ] ) if add_left>0 else left
    result_right = ( [ right, as_segment_context('\n'*add_right) ] if not (detect_format(right)=='(list)') else right + [ as_segment_context('\n'*add_right) ] ) if add_right>0 else right
    return result_left, result_right



class ErrorCantSplitAtomicPiece(Exception):
    """To be called when we can't split a piece"""
def split_piece(
    input: Any,
    start: int,
    end: int,
    to_hash: Callable[[Any],str]
) -> Any:
    """A helper fn for slice_pieces"""
    format = detect_format(input)
    text = to_hash(input)
    if (start == 0) and (end==len(text)):
        return input
    elif (start==0) and (end==0):
        return as_format(None,'(none)',format)
    elif format=='(none)':
        raise Exception(f'Can\'t split (none): this should not be possible, this code should not be reachable, please check: "{input}"[{start}:{end}] ({format})')
    elif format=='(str)':
        return f'{input[start:end]}'
    elif format in ('(list)',):
        pieces = input
        result = []
        cursor = 0
        for piece in pieces:
            text = to_hash(piece)
            piece_start = cursor
            piece_end = cursor + len(text)

            # check overlap
            if piece_end > start and piece_start < end:
                try:
                    local_start = max(start, piece_start) - piece_start
                    local_end = min(end, piece_end) - piece_start

                    if local_start == local_end:
                        # is empty - skip
                        pass
                    elif local_start == 0 and local_end == piece_end:
                        # is a full piece - just append, not split
                        result.append(piece)
                    else:
                        # sub_text = text[local_start:local_end]
                        sub_piece = split_piece(piece,local_start,local_end,to_hash)
                        if not is_empty(sub_piece):
                            result.append(sub_piece)
                    
                except ErrorCantSplitAtomicPiece as e:
                    raise e # what else can I do, other than re-raise # TODO:
            
            cursor = piece_end
            if cursor>end:
                break

        return result
    elif format in ('(propertylist)',):
        # sorry, ugly code
        # test_a = to_hash() # this is literally not possible
        raise ErrorCantSplitAtomicPiece(f'Can\'t split (propertylist): too complicated: "{input}"[{start}:{end}] ({format})')
    elif format in ('(segment)',):
        if 'parts' in input and 'text' not in input:
            return {'role':input.get('role',None),'parts':split_piece(get_segment_payload(input),start,end,to_hash)}
        elif 'text' in input and 'parts' not in input:
            return {'role':input.get('role',None),'text':split_piece(get_segment_payload(input),start,end,to_hash)}
        else:
            assert False, 'Hmm, splitting a piece (segment) but where is the payload, if it\'s not "text" or "parts"?'
    elif format in ('(dict)',):
        raise ErrorCantSplitAtomicPiece(f'Can\'t split (dict): too complicated: "{input}"[{start}:{end}] ({format})')
    else:
        raise ErrorCantSplitAtomicPiece(f'Can\'t split "{input}"[{start}:{end}] ({format}) - this format is not handled or not implemented')




