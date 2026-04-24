

import re

# from collections import namedtuple
from dataclasses import dataclass
from typing import ClassVar
from difflib import SequenceMatcher

from collections import deque # for find_common_format
from itertools import zip_longest




CONFIG_STRUCTURAL_SHORTEN_CTX = 512





def is_empty(s):
    if s==0:
        return False
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









def shorten_ctx(txt):
    is_str = (txt==f'{txt}')
    if not is_str:
        return txt
    if len(txt)>CONFIG_STRUCTURAL_SHORTEN_CTX:
        include_begin = int(CONFIG_STRUCTURAL_SHORTEN_CTX/4) - 1
        if include_begin < 1:
            include_begin = 1
        include_end = include_begin # int(CONFIG_STRUCTURAL_SHORTEN_CTX - (include_begin+1)) - 1
        if include_end < 1:
            include_end = 1
        # include_ellipsis = '... ...'
        # include_ellipsis = txt[include_begin:-include_end]
        include_ellipsis = {'role':'ellipsis','text':txt[include_begin:-include_end]}
        # txt = txt[:include_begin] + include_ellipsis + txt[-include_end:]
        txt = {'parts':[
            txt[:include_begin],
            include_ellipsis,
            txt[-include_end:],
        ]}
    return txt

def wrap_hide_ctx(o):
    result = o
    fmt = detect_format(o)
    if isinstance(o,str):
        result = shorten_ctx(o)
    elif fmt=='(none)':
        result = o
    elif fmt=='(propertylist)':
        result = [{'name':d['name'],'value':wrap_hide_ctx(d['value'])} for d in o]
    elif fmt=='(list)':
        result = [wrap_hide_ctx(d) for d in o]
    elif fmt=='(dict)':
        result = {**o}
        if 'parts' in result:
            result['parts'] = wrap_hide_ctx(o['result'])
        if 'text' in result:
            result['text'] = wrap_hide_ctx(o['result'])
    return {'role':'ctx','text':result}



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




def text_split_words(s):
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
    return s.split("\n")

def diff_normalize(input,flags=None):
    options = flags or {}
    result = [r for r in input]
    if ('ignorewhitespace' in options) and (options['ignorewhitespace']):
        raise NotImplementedError('Ignore whitespace is not implemented in current implementation of diff')
    if ('ignorecase' in options) and (options['ignorecase']):
        result = [r for r in result]
    if ('ignoreaccents' in options) and (options['ignoreaccents']):
        raise NotImplementedError('Ignore accepts is not implemented in current implementation of diff')
    return result







# temporary repeating similar definitions from diff.py so that I can combine rows and it looks similar
@dataclass(frozen=True)
class DiffItemAbstract:
    line: str
    flag: ClassVar[str] = '???'
    def __str__(self):
        return f'{self.flag}: {self.line}'

@dataclass(frozen=True)
class DiffItemKeep(DiffItemAbstract):
    flag: ClassVar[str] = 'keep'

@dataclass(frozen=True)
class DiffItemInsert(DiffItemAbstract):
    flag: ClassVar[str] = 'insert'

@dataclass(frozen=True)
class DiffItemRemove(DiffItemAbstract):
    flag: ClassVar[str] = 'remove'

def as_diff_items_grouped(opcodes, a, b):
    # TODO: looks like it is not used
    result = []
    for tag, i1, i2, j1, j2 in opcodes:
        line = None
        if tag=='equal':
            line = a[i1:i2]
            result += [DiffItemKeep(line)]
        elif tag == 'replace':
            line = a[i1:i2]
            result += [DiffItemRemove(line)]
            line = b[j1:j2]
            result += [DiffItemInsert(line)]
        elif tag == 'insert':
            line = b[j1:j2]
            result += [DiffItemInsert(line)]
        elif tag == 'delete':
            line = a[i1:i2]
            result += [DiffItemRemove(line)]
        else:
            raise Exception(f'Finding combined compiled output file name: Unrecognized piece from diff chunk {tag}')
    return result

def as_diff_items_concatenated(opcodes, a, b):
    result = []
    for tag, i1, i2, j1, j2 in opcodes:
        line = None
        if tag=='equal':
            chunk_ar = a[i1:i2]
            line = None
            for piece in chunk_ar:
                if line is None:
                    line = piece
                else:
                    line += piece
            result += [DiffItemKeep(line)]
        elif tag == 'replace':
            chunk_ar = a[i1:i2]
            line = None
            for piece in chunk_ar:
                if line is None:
                    line = piece
                else:
                    line += piece
            result += [DiffItemRemove(line)]
            chunk_ar = b[j1:j2]
            line = None
            for piece in chunk_ar:
                if line is None:
                    line = piece
                else:
                    line += piece
            result += [DiffItemInsert(line)]
        elif tag == 'insert':
            chunk_ar = b[j1:j2]
            line = None
            for piece in chunk_ar:
                if line is None:
                    line = piece
                else:
                    line += piece
            result += [DiffItemInsert(line)]
        elif tag == 'delete':
            chunk_ar = a[i1:i2]
            line = None
            for piece in chunk_ar:
                if line is None:
                    line = piece
                else:
                    line += piece
            result += [DiffItemRemove(line)]
        else:
            raise Exception(f'Finding combined compiled output file name: Unrecognized piece from diff chunk {tag}')
    return result

def as_diff_items_individual(opcodes, a, b):
    result = []
    for tag, i1, i2, j1, j2 in opcodes:
        line = None
        if tag=='equal':
            line = a[i1:i2]
            for l in line:
                result += [DiffItemKeep(l)]
        elif tag == 'replace':
            line = a[i1:i2]
            for l in line:
                result += [DiffItemRemove(l)]
            line = b[j1:j2]
            for l in line:
                result += [DiffItemInsert(l)]
        elif tag == 'insert':
            line = b[j1:j2]
            for l in line:
                result += [DiffItemInsert(l)]
        elif tag == 'delete':
            line = a[i1:i2]
            for l in line:
                result += [DiffItemRemove(l)]
        else:
            raise Exception(f'Finding combined compiled output file name: Unrecognized piece from diff chunk {tag}')
    return result

def as_diff_items(*args,**argv):
    return as_diff_items_individual(*args,**argv)









def diff_make_combined_list(a,b):
    sm = SequenceMatcher(None,a,b)
    result = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag=='equal':
            result += a[i1:i2]
        elif tag == 'replace':
            result += a[i1:i2]
            result += b[j1:j2]
        elif tag == 'insert':
            result += b[j1:j2]
        elif tag == 'delete':
            result += a[i1:i2]
        else:
            raise Exception(f'Finding combined compiled list of compared collections: Unrecognized piece from diff chunk {tag}')
    return result

def diff_raw(list_l,list_r):
    # # just a wrapper
    # return Myers.diff(list_l,list_r)
    # hmmm, is this still used?
    raise NotImplementedError(f'diff_raw is not implemented; please clarify what actually need as "diff_raw"')









class MDMDiffWrappersGroupingMissingParentException(Exception):
    """Diff: diff item names with groupings: every group must include a parent element"""
def finddiff_row_names_respecting_groups(rows_l,rows_r,delimiter,level=None,flags=None):
    try:
        flags = flags or {}
        rows_inp_l = [ r for r in rows_l ]
        rows_inp_r = [ r for r in rows_r ]
        #grouping_found = False

        # explanation:
        # when we have a row Respondent.Origin.Categories[Scan]
        # we split it to parent group name "Respondent", and everything inside, that is processed recursively
        # and that left part is called a "group", a list of groups is "rows_ungrouped_l" (for the left set) and "rows_ungrouped_r" (for the right set)
        # then, groups_l_defs (resp. groups_r_defs) holds the list of items within each group (where group name is a dict key)
        # For example groups_l_defs['Respondent'] = [ '', 'Serial', 'Origin', 'Origin.Categories[Scan]', 'Origin.Categories[HTMLPlayer]', 'Origin.Categories[DataPlayer]', 'ID', ... ]
        # please note the '' element, there should be an elemetn for just "Respondent", the block item itself, which also has a label and properties and should be in the report

        rows_ungrouped_l = []
        groups_l_defs = {}
        if 'hierarhical_ignore_missing_parent' in flags and flags['hierarhical_ignore_missing_parent']:
            groups_l_defs = {'':[]}
        for row in rows_inp_l:
            does_row_belong_to_group = True # ('.' in row)
            #grouping_found = grouping_found or does_row_belong_to_group
            if not does_row_belong_to_group:
                rows_ungrouped_l.append(row)
            else:
                # matches = re.match(r'^(.*?)\.(.*)$',row if '.' in row else '{parent}.{field}'.format(parent=row,field=''))
                # row_group = matches[1] # '' is a valid key for dict, we'll have groups_l_defs[''], which means parent item for us, and it should include a list ['']
                # row_rest = matches[2]
                row_group = row
                row_rest = ''
                if delimiter is not None:
                    matches = (row if delimiter in row else '{parent}{delimiter}{field}'.format(parent=row,field='',delimiter=delimiter)).split(delimiter,1)
                    row_group = matches[0] # '' is a valid key for dict, we'll have groups_l_defs[''], which means parent item for us, and it should include a list ['']
                    row_rest = matches[1]
                if not (row_group in rows_ungrouped_l):
                    rows_ungrouped_l.append(row_group)
                if not (row_group in dict.keys(groups_l_defs)) or not groups_l_defs[row_group]:
                    groups_l_defs[row_group] = []
                #if row_group!='': # we don't need this condition: even if row_group=='' we still need to have one item in groups_l_defs[row_group]
                groups_l_defs[row_group].append(row_rest)
        rows_ungrouped_r = []
        groups_r_defs = {}
        if 'hierarhical_ignore_missing_parent' in flags and flags['hierarhical_ignore_missing_parent']:
            groups_r_defs = {'':[]}
        for row in rows_inp_r:
            does_row_belong_to_group = True # ('.' in row)
            #grouping_found = grouping_found or does_row_belong_to_group
            if not does_row_belong_to_group:
                rows_ungrouped_r.append(row)
            else:
                # matches = re.match(r'^(.*?)\.(.*)$',row if '.' in row else '{parent}.{field}'.format(parent=row,field=''))
                # row_group = matches[1] # '' is a valid key for dict, we'll have groups_r_defs[''], which means parent item for us, and it should include a list ['']
                # row_rest = matches[2]
                row_group = row
                row_rest = ''
                if delimiter is not None:
                    matches = (row if delimiter in row else '{parent}{delimiter}{field}'.format(parent=row,field='',delimiter=delimiter)).split(delimiter,1)
                    row_group = matches[0] # '' is a valid key for dict, we'll have groups_r_defs[''], which means parent item for us, and it should include a list ['']
                    row_rest = matches[1]
                if not (row_group in rows_ungrouped_r):
                    rows_ungrouped_r.append(row_group)
                if not (row_group in dict.keys(groups_r_defs)) or not groups_r_defs[row_group]:
                    groups_r_defs[row_group] = []
                # if row_group!='': # we don't need this condition: even if row_group=='' we still need to have one item in groups_r_defs[row_group]
                groups_r_defs[row_group].append(row_rest)
        grouping_found = False
        if delimiter is not None:
            if (not ('' in groups_l_defs)) or (not ('' in groups_r_defs)):
                # if 'hierarhical_ignore_missing_parent' in flags and flags['hierarhical_ignore_missing_parent']:
                #     if (not ('' in groups_l_defs)):
                #         groups_l_defs = {'':}
                # else:
                raise MDMDiffWrappersGroupingMissingParentException('diff item names with groupings: every group must include a parent element. For example, if there is "QCData.Flags.Categories...", there should be a parent "QCData.Flags", and its parent "QCData", and its parent "" (a root element, just an empty string)')
        for g in dict.keys(groups_l_defs):
            grouping_found = grouping_found or (len(groups_l_defs[g])>1)
        for g in dict.keys(groups_r_defs):
            grouping_found = grouping_found or (len(groups_r_defs[g])>1)
        _diff = SequenceMatcher( None, diff_normalize(rows_ungrouped_l,flags=flags),diff_normalize(rows_ungrouped_r,flags=flags))
        diff_results = as_diff_items( _diff.get_opcodes(), rows_ungrouped_l, rows_ungrouped_r )
        if not grouping_found:
            return diff_results
        else:
            diff_results_grouping_expanded = []
            for diff_item in diff_results:
                if not (diff_item.line in dict.keys(groups_l_defs)) and not (diff_item.line in dict.keys(groups_r_defs)):
                    diff_results_grouping_expanded.append(diff_item)
                else:
                    if diff_item.flag=='remove':
                        diff_results_grouping_expanded.append(diff_item)
                    else:
                        rows_subgroup_l = groups_l_defs[diff_item.line] if diff_item.line in dict.keys(groups_l_defs) else ['']
                        rows_subgroup_r = groups_r_defs[diff_item.line] if diff_item.line in dict.keys(groups_r_defs) else ['']
                        diff_within_group_missing_parent_part = finddiff_row_names_respecting_groups(rows_subgroup_l,rows_subgroup_r,delimiter,level=diff_item.line,flags=flags)
                        diff_within_group = []
                        item_first_meaning_parent_group = True
                        for diff_item_within_group in diff_within_group_missing_parent_part:
                            item_add = None
                            name_with_parent_part_added = '{parent}{delimiter}{field}'.format(parent=diff_item.line,field=diff_item_within_group.line,delimiter=delimiter) if len(diff_item_within_group.line)>0 else diff_item.line
                            diff_item_which_flag_we_grab = diff_item if item_first_meaning_parent_group else diff_item_within_group
                            if diff_item_which_flag_we_grab.flag=='keep':
                                item_add = DiffItemKeep(name_with_parent_part_added)
                            elif diff_item_which_flag_we_grab.flag=='insert':
                                item_add = DiffItemInsert(name_with_parent_part_added)
                            elif diff_item_which_flag_we_grab.flag=='remove':
                                item_add = DiffItemRemove(name_with_parent_part_added)
                            else:
                                raise AttributeError('which diff flag???')
                            diff_within_group.append(item_add)
                            item_first_meaning_parent_group = False
                        for r in diff_within_group:
                            diff_results_grouping_expanded.append(r)
            return diff_results_grouping_expanded
    except MDMDiffWrappersGroupingMissingParentException as e:
        print('Error: find diff in item names with grouping: failed at {level}: {e}'.format(level=level if level else 'root',e=e))
        raise e












def finddiff_values_propertylist_formatsidebyside( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l):
        cmpdata_l = []
    if is_empty(cmpdata_r):
        cmpdata_r = []
    cmpdata_l_prop_names = [ prop['name'] for prop in cmpdata_l ]
    cmpdata_r_prop_names = [ prop['name'] for prop in cmpdata_r ]
    prop_names_list_combined = diff_make_combined_list(cmpdata_l_prop_names,cmpdata_r_prop_names)
    result_this_col_left = []
    result_this_col_right = []
    cmpdata_l_asdict = {}
    for r in cmpdata_l:
        cmpdata_l_asdict[r['name']] = r['value']
    cmpdata_r_asdict = {}
    for r in cmpdata_r:
        cmpdata_r_asdict[r['name']] = r['value']
    for propname in prop_names_list_combined:
        prop_val_left = {'parts':[]}
        prop_val_right = {'parts':[]}
        if( ( propname in cmpdata_l_prop_names ) and ( propname in cmpdata_r_prop_names ) ):
            value_left = cmpdata_l_asdict[propname]
            value_right = cmpdata_r_asdict[propname]
            if value_left==value_right:
                prop_val_left = value_left
                prop_val_right = value_right
            elif( (len(value_left)>0) and (len(value_right)==0) ):
                # prop_val_left = '<<REMOVED>>' + value_left + '<<ENDREMOVED>>'
                prop_val_left = {'text':value_left,'role':'removed'}
                prop_val_right = ''
            elif( (len(value_left)==0) and (len(value_right)>0) ):
                prop_val_left = ''
                # prop_val_right = '<<ADDED>>' + value_right + '<<ENDADDED>>'
                prop_val_right = {'text':value_right,'role':'added'}
            else:
                prop_val_left, prop_val_right = finddiff_values_text_formatsidebyside(value_left,value_right)
        elif( propname in cmpdata_l_prop_names ):
            value_left = cmpdata_l_asdict[propname]
            prop_val_left = {'text':value_left,'role':'removed'}
        elif( propname in cmpdata_r_prop_names ):
            value_right = cmpdata_r_asdict[propname]
            prop_val_right = {'text':value_right,'role':'added'}
        if propname in cmpdata_l_prop_names:
            result_this_col_left.append({'name':propname,'value':prop_val_left})
        if propname in cmpdata_r_prop_names:
            result_this_col_right.append({'name':propname,'value':prop_val_right})
    return result_this_col_left, result_this_col_right


def finddiff_values_text_formatsidebyside( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l):
        cmpdata_l = ''
    if is_empty(cmpdata_r):
        cmpdata_r = ''
    result_this_col_left = cmpdata_l
    result_this_col_right = cmpdata_r
    if cmpdata_l==cmpdata_r:
        result_this_col_left = cmpdata_l
        result_this_col_right = cmpdata_r
    elif( (len(cmpdata_l)>0) and (len(cmpdata_r)==0) ):
        # result_this_col_left = '<<REMOVED>>' + cmpdata_l + '<<ENDREMOVED>>'
        # result_this_col_right = ''
        result_this_col_left = {'parts':[{'text':cmpdata_l,'role':'removed'}]}
        result_this_col_right = {'parts':[]}
    elif( (len(cmpdata_l)==0) and (len(cmpdata_r)>0) ):
        # result_this_col_left = ''
        # result_this_col_right = '<<ADDED>>' + cmpdata_r + '<<ENDADDED>>'
        result_this_col_left = {'parts':[]}
        result_this_col_right = {'parts':[{'text':cmpdata_r,'role':'added'}]}
    else:
        cmpdata_l_into_lines = [ ('' if linenumber==0 else '\n') + (line if len(line)>0 else ' ') for linenumber,line in enumerate(text_split_lines(cmpdata_l)) ]
        cmpdata_r_into_lines = [ ('' if linenumber==0 else '\n') + (line if len(line)>0 else ' ') for linenumber,line in enumerate(text_split_lines(cmpdata_r)) ]
        diff_data = SequenceMatcher(None,cmpdata_l_into_lines,cmpdata_r_into_lines).get_opcodes()
        diff_data = as_diff_items_concatenated( diff_data, cmpdata_l_into_lines, cmpdata_r_into_lines )
        diff_data_l_and_r_by_lines = []
        for part in diff_data:
            if part.flag=='keep':
                diff_data_l_and_r_by_lines.append({'l':part.line,'r':part.line})
            elif part.flag=='insert':
                if( (len(diff_data_l_and_r_by_lines)>0) and (diff_data_l_and_r_by_lines[-1]['r']=='') ):
                    diff_data_l_and_r_by_lines[-1]['r'] = part.line
                else:
                    diff_data_l_and_r_by_lines.append({'l':'','r':part.line})
            elif part.flag=='remove':
                if( (len(diff_data_l_and_r_by_lines)>0) and (diff_data_l_and_r_by_lines[-1]['l']=='') ):
                    diff_data_l_and_r_by_lines[-1]['l'] = part.line
                else:
                    diff_data_l_and_r_by_lines.append({'l':part.line,'r':''})
        result_this_col_left = {'parts':[]}
        result_this_col_right = {'parts':[]}
        for linenumber,part in enumerate(diff_data_l_and_r_by_lines):
            # if linenumber>0:
            #     result_this_col_left['parts'].append( '\n' )
            #     result_this_col_right['parts'].append( '\n' )
            cmpdata_l_into_pieces = text_split_words(part['l'])
            cmpdata_r_into_pieces = text_split_words(part['r'])
            diff_data = as_diff_items_concatenated( SequenceMatcher(None,cmpdata_l_into_pieces,cmpdata_r_into_pieces).get_opcodes(), cmpdata_l_into_pieces, cmpdata_r_into_pieces )
            for part in diff_data:
                if part.flag=='keep':
                    result_this_col_left['parts'].append(part.line)
                    result_this_col_right['parts'].append(part.line)
                elif part.flag=='insert':
                    txt_lines = part.line.split('\n')
                    result_this_col_left['parts'].append( {'text':'\n '.join('' for p in txt_lines)} )
                    result_this_col_right['parts'].append( {'text':'\n'.join((p if len(p)>0 else ' ') for p in txt_lines),'role':'added'} )
                elif part.flag=='remove':
                    txt_lines = part.line.split('\n')
                    result_this_col_left['parts'].append( {'text':'\n'.join((p if len(p)>0 else ' ') for p in txt_lines),'role':'removed'} )
                    result_this_col_right['parts'].append( {'text':'\n '.join('' for p in txt_lines)} )
                # const_test_l_before = len(re.findall(r'\n',result_this_col_left))
                # const_test_r_before = len(re.findall(r'\n',result_this_col_right))
                # if const_test_l_before!=const_test_r_before:
                #     # assert line break counts
                # print('linebreaks: {nl} (left), {nr} (right), processing part: {p}'.format(nl=const_test_l_before,nr=const_test_r_before,p=part.line))
        # if result_this_col_left['parts'][-1]=='\n':
        #     result_this_col_left['parts'] = result_this_col_left['parts'][:-1]
        # else:
        #     raise Exception('last part should be \\n, as per my understanding, please check')
        # if result_this_col_right['parts'][-1]=='\n':
        #     result_this_col_right['parts'] = result_this_col_right['parts'][:-1]
        # else:
        #     raise Exception('last part should be \\n, as per my understanding, please check')
    return result_this_col_left, result_this_col_right

def finddiff_values_list_formatsidebyside( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l):
        cmpdata_l = []
    if is_empty(cmpdata_r):
        cmpdata_r = []
    cmpdata_l_hashed = [f'{v}' for v in cmpdata_l]
    cmpdata_r_hashed = [f'{v}' for v in cmpdata_r]
    # list_combined = diff_make_combined_list( cmpdata_l_hashed, cmpdata_r_hashed )
    sm = SequenceMatcher( None,cmpdata_l_hashed, cmpdata_r_hashed )
    result_l = []
    result_r = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        items_l = cmpdata_l[i1:i2]
        items_r = cmpdata_r[j1:j2]
        list_combined = list(zip_longest(items_l, items_r))
        for item_l, item_r in list_combined:
            item = finddiff_values_general_formatcombined( item_l, item_r )
            if tag == 'equal':
                result_l.append({'text':item})
                result_r.append({'text':item})
            elif tag == 'replace':
                result_l.append({'text':item_l,'role':'removed'})
                result_r.append({'text':item_r,'role':'added'})
            elif tag == 'insert':
                result_r.append({'text':item_r,'role':'added'})
            elif tag == 'delete':
                result_l.append({'text':item_l,'role':'removed'})
    return result_l, result_r

def finddiff_values_dict_formatsidebyside( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l):
        cmpdata_l = {}
    if is_empty(cmpdata_r):
        cmpdata_r = {}
    props_left = [prop for prop in dict.keys(cmpdata_l)]
    props_right = [prop for prop in dict.keys(cmpdata_r)]
    props_combined = diff_make_combined_list( props_left, props_right )
    result_l = {}
    result_r = {}
    for prop in props_combined:
        value_left = cmpdata_l[prop] if prop in cmpdata_l else None
        value_right = cmpdata_r[prop] if prop in cmpdata_r else None
        value_resulting_l, value_resulting_r = finddiff_values_general_formatsidebyside( value_left, value_right )
        if prop in cmpdata_l:
            result_l[prop] = value_resulting_l
        if prop in cmpdata_r:
            result_r[prop] = value_resulting_r
    return result_l,result_r

def finddiff_values_general_formatsidebyside( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l) and is_empty(cmpdata_r):
        return '',''
    else:
        cmpdata_l_format = detect_format(cmpdata_l)
        cmpdata_r_format = detect_format(cmpdata_r)
        common_format = find_common_format_denominator_with_fallback_str(cmpdata_l_format,cmpdata_r_format)
        cmpdata_l = as_format(cmpdata_l,cmpdata_l_format,common_format)
        cmpdata_r = as_format(cmpdata_r,cmpdata_r_format,common_format)
        cmpdata_l_format = common_format
        cmpdata_r_format = common_format
        if cmpdata_l_format=='(none)':
            cmpdata_l_format = cmpdata_r_format
        if cmpdata_r_format=='(none)':
            cmpdata_r_format = cmpdata_l_format
        if (cmpdata_l_format==cmpdata_r_format):
            if cmpdata_l_format=='(str)':
                return finddiff_values_text_formatsidebyside( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='(list)':
                return finddiff_values_list_formatsidebyside( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='(dict)':
                # cmpdata_l = clean_role_underlying(cmpdata_l)
                # cmpdata_r = clean_role_underlying(cmpdata_r)
                if 'role' in cmpdata_l and cmpdata_l['role']=='ctx' and 'ctx' in cmpdata_r and cmpdata_r['role']=='ctx':
                    return cmpdata_r, cmpdata_r
                return finddiff_values_dict_formatsidebyside( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='(propertylist)':
                return finddiff_values_propertylist_formatsidebyside( cmpdata_l, cmpdata_r )
            else:
                return finddiff_values_general_formatsidebyside( '{f}'.format(f=cmpdata_l), '{f}'.format(f=cmpdata_r) )
        else:
            return finddiff_values_general_formatsidebyside( '{f}'.format(f=cmpdata_l), '{f}'.format(f=cmpdata_r) )






def finddiff_values_propertylist_formatcombined( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l):
        cmpdata_l = []
    if is_empty(cmpdata_r):
        cmpdata_r = []
    cmpdata_l_prop_names = [ prop['name'] for prop in cmpdata_l ]
    cmpdata_r_prop_names = [ prop['name'] for prop in cmpdata_r ]
    prop_names_list_combined = diff_make_combined_list(cmpdata_l_prop_names,cmpdata_r_prop_names)
    result_this_col_combined = []
    cmpdata_l_asdict = {}
    for r in cmpdata_l:
        cmpdata_l_asdict[r['name']] = r['value']
    cmpdata_r_asdict = {}
    for r in cmpdata_r:
        cmpdata_r_asdict[r['name']] = r['value']
    for propname in prop_names_list_combined:
        value_left = cmpdata_l_asdict[propname] if propname in cmpdata_l_asdict else ''
        value_right = cmpdata_r_asdict[propname] if propname in cmpdata_r_asdict else ''
        result_this_col_combined.append({'name':propname,'value':finddiff_values_general_formatcombined(value_left,value_right)})
    return result_this_col_combined

def finddiff_values_text_formatcombined( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l):
        cmpdata_l = ''
    if is_empty(cmpdata_r):
        cmpdata_r = ''
    result_this_col_combined = {'parts':[]}
    if cmpdata_l==cmpdata_r:
        result_this_col_combined = wrap_hide_ctx( cmpdata_l )
    elif( (len(cmpdata_l)>0) and (len(cmpdata_r)==0) ):
        result_this_col_combined = {'text':cmpdata_l,'role':'removed'}
    elif( (len(cmpdata_l)==0) and (len(cmpdata_r)>0) ):
        result_this_col_combined = {'text':cmpdata_r,'role':'added'}
    else:
        cmpdata_l_into_lines = [ ('' if linenumber==0 else '\n') + (line if len(line)>0 else ' ') for linenumber,line in enumerate(text_split_lines(cmpdata_l)) ]
        cmpdata_r_into_lines = [ ('' if linenumber==0 else '\n') + (line if len(line)>0 else ' ') for linenumber,line in enumerate(text_split_lines(cmpdata_r)) ]
        diff_data = SequenceMatcher(None,cmpdata_l_into_lines,cmpdata_r_into_lines).get_opcodes()
        diff_data = as_diff_items_concatenated( diff_data, cmpdata_l_into_lines, cmpdata_r_into_lines )
        diff_data_l_and_r_by_lines = []
        for part in diff_data:
            if part.flag=='keep':
                diff_data_l_and_r_by_lines.append({'l':part.line,'r':part.line})
            elif part.flag=='insert':
                if( (len(diff_data_l_and_r_by_lines)>0) and (diff_data_l_and_r_by_lines[-1]['r']=='') ):
                    diff_data_l_and_r_by_lines[-1]['r'] = part.line
                else:
                    diff_data_l_and_r_by_lines.append({'l':'','r':part.line})
            elif part.flag=='remove':
                if( (len(diff_data_l_and_r_by_lines)>0) and (diff_data_l_and_r_by_lines[-1]['l']=='') ):
                    diff_data_l_and_r_by_lines[-1]['l'] = part.line
                else:
                    diff_data_l_and_r_by_lines.append({'l':part.line,'r':''})
        result_this_col_combined = {'parts':[]}
        for linenumber,part in enumerate(diff_data_l_and_r_by_lines):
            # if linenumber>0:
            #     result_this_col_combined['parts'].append( '\n' )
            cmpdata_l_into_pieces = text_split_words(part['l'])
            cmpdata_r_into_pieces = text_split_words(part['r'])
            diff_data = as_diff_items_concatenated( SequenceMatcher(None,cmpdata_l_into_pieces,cmpdata_r_into_pieces).get_opcodes(), cmpdata_l_into_pieces, cmpdata_r_into_pieces )
            for part in diff_data:
                if part.flag=='keep':
                    result_this_col_combined['parts'].append(part.line)
                elif part.flag=='insert':
                    result_this_col_combined['parts'].append( {'text':part.line,'role':'added'} )
                elif part.flag=='remove':
                    result_this_col_combined['parts'].append( {'text':part.line,'role':'removed'} )
    return result_this_col_combined

def finddiff_values_list_formatcombined( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l):
        cmpdata_l = []
    if is_empty(cmpdata_r):
        cmpdata_r = []
    cmpdata_l_hashed = [f'{v}' for v in cmpdata_l]
    cmpdata_r_hashed = [f'{v}' for v in cmpdata_r]
    # list_combined = diff_make_combined_list( cmpdata_l_hashed, cmpdata_r_hashed )
    sm = SequenceMatcher( None,cmpdata_l_hashed, cmpdata_r_hashed )
    result = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        items_l = cmpdata_l[i1:i2]
        items_r = cmpdata_r[j1:j2]
        list_combined = list(zip_longest(items_l, items_r))
        for item_l, item_r in list_combined:
            item = finddiff_values_general_formatcombined( item_l, item_r )
            if tag == 'equal':
                result.append({'text':item})
            elif tag == 'replace':
                result.append({'text':item_l,'role':'removed'})
                result.append({'text':item_r,'role':'added'})
            elif tag == 'insert':
                result.append({'text':item_r,'role':'added'})
            elif tag == 'delete':
                result.append({'text':item_l,'role':'removed'})
    return result

def finddiff_values_dict_formatcombined( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l):
        cmpdata_l = {}
    if is_empty(cmpdata_r):
        cmpdata_r = {}
    props_left = [prop for prop in dict.keys(cmpdata_l)]
    props_right = [prop for prop in dict.keys(cmpdata_r)]
    props_combined = diff_make_combined_list( props_left, props_right )
    result = {}
    for prop in props_combined:
        value_left = cmpdata_l[prop] if prop in cmpdata_l else None
        value_right = cmpdata_r[prop] if prop in cmpdata_r else None
        value_resulting = finddiff_values_general_formatcombined( value_left, value_right )
        result[prop] = value_resulting
    return result

def finddiff_values_general_formatcombined( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l) and is_empty(cmpdata_r):
        # return '' # wrong, if we compare {}'s, or {} to None, the result should be of the same type, not str
        # return None # and this is wrong too
        cmpdata_l_format = detect_format(cmpdata_l,avoid_none=True)
        cmpdata_r_format = detect_format(cmpdata_r,avoid_none=True)
        common_format = find_common_format_denominator_with_fallback_str(cmpdata_l_format,cmpdata_r_format)
        cmpdata_l = as_format(cmpdata_l,cmpdata_l_format,common_format)
        cmpdata_r = as_format(cmpdata_r,cmpdata_r_format,common_format)
        cmpdata_l_format = common_format
        cmpdata_r_format = common_format
        if (cmpdata_l_format==cmpdata_r_format):
            if cmpdata_l_format=='(str)':
                return ''
            elif cmpdata_l_format=='(list)':
                return []
            elif cmpdata_l_format=='(dict)':
                return {}
            elif cmpdata_l_format=='(propertylist)':
                return []
            else:
                return None
        else:
            return None
    else:
        cmpdata_l_format = detect_format(cmpdata_l)
        cmpdata_r_format = detect_format(cmpdata_r)
        common_format = find_common_format_denominator_with_fallback_str(cmpdata_l_format,cmpdata_r_format)
        cmpdata_l = as_format(cmpdata_l,cmpdata_l_format,common_format)
        cmpdata_r = as_format(cmpdata_r,cmpdata_r_format,common_format)
        cmpdata_l_format = common_format
        cmpdata_r_format = common_format
        if (cmpdata_l_format==cmpdata_r_format):
            if cmpdata_l_format=='(str)':
                return finddiff_values_text_formatcombined( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='(list)':
                return finddiff_values_list_formatcombined( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='(dict)':
                # cmpdata_l = clean_role_underlying(cmpdata_l)
                # cmpdata_r = clean_role_underlying(cmpdata_r)
                if 'role' in cmpdata_l and cmpdata_l['role']=='ctx' and 'ctx' in cmpdata_r and cmpdata_r['role']=='ctx':
                    if cmpdata_l==cmpdata_r:
                        return cmpdata_l
                    else:
                        return wrap_hide_ctx('... ...')
                return finddiff_values_dict_formatcombined( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='(propertylist)':
                return finddiff_values_propertylist_formatcombined( cmpdata_l, cmpdata_r )
            else:
                return finddiff_values_general_formatcombined( '{f}'.format(f=cmpdata_l), '{f}'.format(f=cmpdata_r) )
        else:
            return finddiff_values_general_formatcombined( '{f}'.format(f=cmpdata_l), '{f}'.format(f=cmpdata_r) )






def finddiff_values_propertylist_formatstructural( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l):
        cmpdata_l = []
    if is_empty(cmpdata_r):
        cmpdata_r = []
    cmpdata_l_prop_names = [ prop['name'] for prop in cmpdata_l ]
    cmpdata_r_prop_names = [ prop['name'] for prop in cmpdata_r ]
    prop_names_list_combined = diff_make_combined_list(cmpdata_l_prop_names,cmpdata_r_prop_names)
    result_this_col_combined = []
    cmpdata_l_asdict = {}
    for r in cmpdata_l:
        cmpdata_l_asdict[r['name']] = r['value']
    cmpdata_r_asdict = {}
    for r in cmpdata_r:
        cmpdata_r_asdict[r['name']] = r['value']
    for propname in prop_names_list_combined:
        value_left = cmpdata_l_asdict[propname] if propname in cmpdata_l_asdict else ''
        value_right = cmpdata_r_asdict[propname] if propname in cmpdata_r_asdict else ''
        value = finddiff_values_general_formatstructural(value_left,value_right)
        did_change = not(value_left==value_right) # did_contents_change_deep_inspect(value) # TODO: only print changed in structural?
        if did_change:
            result_this_col_combined.append({'name':propname,'value':value})
        else:
            # result_this_col_combined.append({'name':propname,'value':wrap_hide_ctx(value)})
            pass
    return result_this_col_combined

def finddiff_values_text_formatstructural( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l):
        cmpdata_l = ''
    if is_empty(cmpdata_r):
        cmpdata_r = ''
    result_this_col_combined = {'parts':[]}
    if cmpdata_l==cmpdata_r:
        result_this_col_combined = None
    elif( (len(cmpdata_l)>0) and (len(cmpdata_r)==0) ):
        result_this_col_combined = {'text':cmpdata_l,'role':'removed'}
    elif( (len(cmpdata_l)==0) and (len(cmpdata_r)>0) ):
        result_this_col_combined = {'text':cmpdata_r,'role':'added'}
    else:
        cmpdata_l_into_lines = [ ('' if linenumber==0 else '\n') + (line if len(line)>0 else ' ') for linenumber,line in enumerate(text_split_lines(cmpdata_l)) ]
        cmpdata_r_into_lines = [ ('' if linenumber==0 else '\n') + (line if len(line)>0 else ' ') for linenumber,line in enumerate(text_split_lines(cmpdata_r)) ]
        diff_data = SequenceMatcher(None,cmpdata_l_into_lines,cmpdata_r_into_lines).get_opcodes()
        diff_data = as_diff_items_concatenated( diff_data, cmpdata_l_into_lines, cmpdata_r_into_lines )
        diff_data_l_and_r_by_lines = []
        for part in diff_data:
            if part.flag=='keep':
                diff_data_l_and_r_by_lines.append({'l':part.line,'r':part.line})
            elif part.flag=='insert':
                if( (len(diff_data_l_and_r_by_lines)>0) and (diff_data_l_and_r_by_lines[-1]['r']=='') ):
                    diff_data_l_and_r_by_lines[-1]['r'] = part.line
                else:
                    diff_data_l_and_r_by_lines.append({'l':'','r':part.line})
            elif part.flag=='remove':
                if( (len(diff_data_l_and_r_by_lines)>0) and (diff_data_l_and_r_by_lines[-1]['l']=='') ):
                    diff_data_l_and_r_by_lines[-1]['l'] = part.line
                else:
                    diff_data_l_and_r_by_lines.append({'l':part.line,'r':''})
        result_this_col_combined = {'parts':[]}
        for linenumber,part in enumerate(diff_data_l_and_r_by_lines):
            # if linenumber>0:
            #     result_this_col_combined['parts'].append( '\n' )
            cmpdata_l_into_pieces = text_split_words(part['l'])
            cmpdata_r_into_pieces = text_split_words(part['r'])
            diff_data = as_diff_items_concatenated( SequenceMatcher(None,cmpdata_l_into_pieces,cmpdata_r_into_pieces).get_opcodes(), cmpdata_l_into_pieces, cmpdata_r_into_pieces )
            for part in diff_data:
                if part.flag=='keep':
                    result_this_col_combined['parts'].append(wrap_hide_ctx(part.line))
                elif part.flag=='insert':
                    result_this_col_combined['parts'].append( {'text':part.line,'role':'added'} )
                elif part.flag=='remove':
                    result_this_col_combined['parts'].append( {'text':part.line,'role':'removed'} )
            # result_this_col_combined = {
            #     **result_this_col_combined,
            #     'parts': [
            #         wrap_hide_ctx(chunk) for chunk in result_this_col_combined['parts']
            #     ]
            # }
    return result_this_col_combined

def finddiff_values_list_formatstructural( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l):
        cmpdata_l = []
    if is_empty(cmpdata_r):
        cmpdata_r = []
    cmpdata_l_hashed = [f'{v}' for v in cmpdata_l]
    cmpdata_r_hashed = [f'{v}' for v in cmpdata_r]
    # list_combined = diff_make_combined_list( cmpdata_l_hashed, cmpdata_r_hashed )
    sm = SequenceMatcher( None,cmpdata_l_hashed, cmpdata_r_hashed )
    result = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        items_l = cmpdata_l[i1:i2]
        items_r = cmpdata_r[j1:j2]
        list_combined = list(zip_longest(items_l, items_r))
        for item_l, item_r in list_combined:
            item = finddiff_values_general_formatstructural( item_l, item_r )
            if tag == 'equal':
                result.append({'text':item})
            elif tag == 'replace':
                result.append({'text':item_r,'role':'added'})
                result.append({'text':item_l,'role':'removed'})
            elif tag == 'insert':
                result.append({'text':item_r,'role':'added'})
            elif tag == 'delete':
                result.append({'text':item_l,'role':'removed'})
    return result

def finddiff_values_dict_formatstructural( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l):
        cmpdata_l = {}
    if is_empty(cmpdata_r):
        cmpdata_r = {}
    props_left = [prop for prop in dict.keys(cmpdata_l)]
    props_right = [prop for prop in dict.keys(cmpdata_r)]
    props_combined = diff_make_combined_list( props_left, props_right )
    result = {}
    for prop in props_combined:
        value_left = cmpdata_l[prop] if prop in cmpdata_l else None
        value_right = cmpdata_r[prop] if prop in cmpdata_r else None
        value_resulting = finddiff_values_general_formatstructural( value_left, value_right )
        did_change = not(value_left==value_right)
        if did_change:
            result[prop] = value_resulting
    return result

def finddiff_values_general_formatstructural( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l) and is_empty(cmpdata_r):
        # return '' # wrong, if we compare {}'s, or {} to None, the result should be of the same type, not str
        # return None # and this is wrong too
        cmpdata_l_format = detect_format(cmpdata_l,avoid_none=True)
        cmpdata_r_format = detect_format(cmpdata_r,avoid_none=True)
        common_format = find_common_format_denominator_with_fallback_str(cmpdata_l_format,cmpdata_r_format)
        cmpdata_l = as_format(cmpdata_l,cmpdata_l_format,common_format)
        cmpdata_r = as_format(cmpdata_r,cmpdata_r_format,common_format)
        cmpdata_l_format = common_format
        cmpdata_r_format = common_format
        if (cmpdata_l_format==cmpdata_r_format):
            if cmpdata_l_format=='(str)':
                return ''
            elif cmpdata_l_format=='(list)':
                return []
            elif cmpdata_l_format=='(dict)':
                return {}
            elif cmpdata_l_format=='(propertylist)':
                return []
            else:
                return None
        else:
            return None
    else:
        cmpdata_l_format = detect_format(cmpdata_l)
        cmpdata_r_format = detect_format(cmpdata_r)
        common_format = find_common_format_denominator_with_fallback_str(cmpdata_l_format,cmpdata_r_format)
        cmpdata_l = as_format(cmpdata_l,cmpdata_l_format,common_format)
        cmpdata_r = as_format(cmpdata_r,cmpdata_r_format,common_format)
        cmpdata_l_format = common_format
        cmpdata_r_format = common_format
        if (cmpdata_l_format==cmpdata_r_format):
            if cmpdata_l_format=='(str)':
                return finddiff_values_text_formatstructural( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='(list)':
                return finddiff_values_list_formatstructural( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='(dict)':
                # cmpdata_l = clean_role_underlying(cmpdata_l)
                # cmpdata_r = clean_role_underlying(cmpdata_r)
                if 'role' in cmpdata_l and cmpdata_l['role']=='ctx' and 'ctx' in cmpdata_r and cmpdata_r['role']=='ctx':
                    if cmpdata_l==cmpdata_r:
                        return cmpdata_l
                    else:
                        return wrap_hide_ctx('... ...')
                return finddiff_values_dict_formatstructural( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='(propertylist)':
                return finddiff_values_propertylist_formatstructural( cmpdata_l, cmpdata_r )
            else:
                return finddiff_values_general_formatstructural( '{f}'.format(f=cmpdata_l), '{f}'.format(f=cmpdata_r) )
        else:
            return finddiff_values_general_formatstructural( '{f}'.format(f=cmpdata_l), '{f}'.format(f=cmpdata_r) )

