

from collections import deque # for find_common_format
import re





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

def text_split_lines(s):
    """Splits continuous text into pieces, separated with newline characters"""
    return f'{s}'.split("\n")




class ErrorDiffClassesNotPossibleToDetect(Exception):
    """Raised when segment type can't be detected
    
    "Segments" are specific type of output diff is producing.
    It is basically a dict with "role" indicating segment role
    
    "Role" indicates its type - if it's an "change" block (with something added/removed), or "context" that is not reported
    as actual result, but is still needed to show where the change block is located

    This is only important when we call diff on diffs. So we need to filter inputs and identify "segment types" first. If something
    is a "change" block - we process it. If something is "context" - we pass through. If else - not sure, that's where we catch this exception and see what we can do/should do
    """
def detect_diffsegment_str_type(input: str):
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
def detect_diffsegment_type(input):
    """A function to detect segment type
    
    "Segments" are specific type of output diff is producing.
    It is basically a dict with "role" indicating segment role
    
    "Role" indicates its type - if it's an "change" block (with something added/removed), or "context" that is not reported
    as actual result, but is still needed to show where the change block is located

    This is only important when we call diff on diffs. So we need to filter inputs and identify "segment types" first. If something
    is a "change" block - we process it. If something is "context" - we pass through. If else - not sure, we'll raise and exception and handle it and see what we can do/should do
    """
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
            return detect_diffsegment_type(input['parts'])
        elif 'text' in input:
            return detect_diffsegment_type(input['text'])
        else:
            raise ErrorDiffClassesNotPossibleToDetect(f'Each returned segment must clearly identify if it\'s a "change" segment or "context" segment: {input} of type {detect_format(input)}')
    elif input_fmt == '(none)':
        return None
    elif input_fmt == '(propertylist)':
        context_found = False
        change_found = False
        for row in input:
            piece = row['value']
            piece_type = detect_diffsegment_type(piece)
            change_found = change_found or piece_type == 'change'
            context_found = context_found or piece_type == 'context'
            assert (piece_type in ('change','context','blank',)) or (piece_type is None and is_empty(piece)), 'Failed: each piece should be ChangeBlock or ContextBlock, or be empty'
        return 'change' if change_found else 'context'
    elif input_fmt == '(list)':
        context_found = False
        change_found = False
        for piece in input:
            piece_type = detect_diffsegment_type(piece)
            change_found = change_found or piece_type == 'change'
            context_found = context_found or piece_type == 'context'
            assert (piece_type in ('change','context','blank',)) or (piece_type is None and is_empty(piece)), 'Failed: each piece should be ChangeBlock or ContextBlock, or be empty'
        return 'change' if change_found else 'context'
    elif input_fmt == '(str)':
        return detect_diffsegment_str_type(input)
    raise ErrorDiffClassesNotPossibleToDetect(f'Each returned segment must clearly identify if it\'s a "change" segment or "context" segment: {input} of type {detect_format(input)}')

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
    if isinstance(input,dict):
        role = input.get('role',None)
        result = {**input}
        if role in ('added','removed'):
            # roles_prev = input.get('roles_prev',[])
            # roles_prev.append(role)
            # result['role'] = None
            # result['roles_prev'] = roles_prev
            result['role'] = f'source_{result["role"]}'
        # if 'parts' in input and detect_format(input['parts']) in ['(list)','(propertylist)']:
        if 'parts' in input:
            result['parts'] =  normalize_input_relocate_diff_markers(result['parts'])
        if 'text' in input:
            result['text'] =  normalize_input_relocate_diff_markers(result['text'])
        if 'text' not in result and 'parts' not in result:
            raise Exception(f'Can\' filter prev inputs and clean from prev diff classes: {input} of type {input_fmt}')
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
    return detect_diffsegment_type(input) == 'change'





def is_empty(input):
    """Responds to question if there is any content inside

    Mostly same as simply "not not input", but does not trigger zero as empty/missing value.
    Cause zero is content, while empty string, or empty dict, or "None", are not."""
    if input==0:
        return False
    elif is_diff_segment_dict(input):
        if not input:
            return True
        if 'text' in input and not is_empty(input['text']):
            return False
        if 'parts' in input and not is_empty(input['parts']):
            return False
        return True
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
        return detect_diffsegment_type(input)=='context'
    except:
        return False

def detect_diffsegment_type_noncompulsory(input):
    """Helps to detect segment type

    Basically, same as detect_diffsegment_type. But detect_diffsegment_type raises an exception, if inputs
    are not in fact segments and don't indicate segment type. Here, this is just a safe wrapper. If something
    is "context" or "change block", this fn will return its type. If inputs are whatever different, this fn just returns None.
    
    "Segments" are specific type of output diff is producing.
    It is basically a dict with "role" indicating segment role
    
    "Role" indicates its type - if it's an "change" block (with something added/removed), or "context" that is not reported
    as actual result, but is still needed to show where the change block is located

    This is only important when we call diff on diffs. This way we can capture if inputs contain something significant ("change block"), or just "context"
    """
    try:
        return detect_diffsegment_type(input)
    except:
        return None

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
            if not input:
                return True
            if 'text' in input and not is_empty(input['text']):
                return False
            if 'parts' in input and not is_empty(input['parts']):
                return False
            return True
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
    elif is_diff_segment_dict(inp_value) and 'text' in inp_value:
        return as_plain_text(inp_value['text'])
    elif is_diff_segment_dict(inp_value) and 'parts' in inp_value:
        return as_plain_text(inp_value['parts'])
    elif isinstance(inp_value,list):
        return ''.join([as_plain_text(s) for s in inp_value])
    else:
        return f'{inp_value}'

def as_hash(input):
    "Takes input, and generates a hashable tuple, that consists of 1. segment type, 2. text content, rendered all as plain text without roles or formatting"
    value = as_plain_text(input)
    role = detect_diffsegment_type_noncompulsory(input)
    return (role,value)


def count_linebreaks(input):
    """Counts how many lines there will be when this piece is rendered as plain text, without any roles or formatting"""
    return len(text_split_lines(as_plain_text(input)))

def fill_same_number_linebreaks(left,right):
    """Appends necessary number of line breaks to either left or right input, so that they maatch in number of lines they occupy"""
    len_left = count_linebreaks(left)
    len_right = count_linebreaks(right)
    len_common = len_left if len_left > len_right else len_right
    add_left = len_common - len_left
    add_right = len_common - len_right
    result_left = ( [ left, as_segment_context('\n'*add_left) ] if not (detect_format(left)=='(list)') else left + [ as_segment_context('\n'*add_left) ] ) if add_left>0 else left
    result_right = ( [ right, as_segment_context('\n'*add_right) ] if not (detect_format(right)=='(list)') else right + [ as_segment_context('\n'*add_right) ] ) if add_right>0 else right
    return result_left, result_right



