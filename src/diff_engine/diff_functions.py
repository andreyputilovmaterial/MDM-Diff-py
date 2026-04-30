

import re


# from collections import namedtuple
from dataclasses import dataclass
from typing import ClassVar
from difflib import SequenceMatcher

from itertools import zip_longest




from .common_functions import (
    as_format,
    detect_format,
    # find_common_format_denominator,
    find_common_format_denominator_with_fallback_str,
    is_empty,
    is_property_list,
    is_diff_segment_dict,
    is_segment_context,
    detect_diffsegment_type_noncompulsory,
    as_segment_context,
    as_segment_change,
)




CONFIG_STRUCTURAL_SHORTEN_CTX = 512
















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
    return f'{s}'.split("\n")

def diff_normalize(input,flags=None):
    options = flags or {}
    result = [r for r in input]
    if ('ignorewhitespace' in options) and (options['ignorewhitespace']):
        raise NotImplementedError('Ignore whitespace is not implemented in current implementation of diff')
    if ('ignorecase' in options) and (options['ignorecase']):
        result = [r.lower() for r in result]
    if ('ignoreaccents' in options) and (options['ignoreaccents']):
        raise NotImplementedError('Ignore accepts is not implemented in current implementation of diff')
    return result







# TODO: stop working through these proxies DiffItemXxx - I think this is unnecessary, we can work with SequenceMatcher results directly (logged as issue #10)
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
        # TODO: stop working through these proxies DiffItemXxx - I think this is unnecessary, we can work with SequenceMatcher results directly (logged as issue #10)
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
    result_left = []
    result_right = []
    cmpdata_l_asdict = { record['name']: record['value'] for record in cmpdata_l }
    cmpdata_r_asdict = { record['name']: record['value'] for record in cmpdata_r }
    for propname in prop_names_list_combined:
        value_left = cmpdata_l_asdict.get(propname,None)
        value_right = cmpdata_r_asdict.get(propname,None)
        if( ( propname in cmpdata_l_prop_names ) and ( propname in cmpdata_r_prop_names ) ):
            if value_left==value_right:
                value_left = as_segment_context(value_left)
                value_right = as_segment_context(value_right)
            # elif( not is_empty(value_left) and is_empty(value_right) ):
            #     value_left = as_segment_change(value_left,op='removed') if not is_segment_context(value_left) else value_left
            #     value_right = as_format(None,'(none)',detect_format(value_left))
            # elif( is_empty(value_left) and not is_empty(value_right) ):
            #     value_left = as_format(None,'(none)',detect_format(value_right))
            #     value_right = as_segment_change(value_right,op='added') if not is_segment_context(value_right) else value_right
            else:
                value_left, value_right = finddiff_values_general_formatsidebyside(value_left,value_right)
        elif( propname in cmpdata_l_prop_names ):
            value_left = as_segment_change(value_left,op='removed') if not is_segment_context(value_left) else value_left
        elif( propname in cmpdata_r_prop_names ):
            value_right = as_segment_change(value_right,op='added') if not is_segment_context(value_right) else value_right
        if propname in cmpdata_l_prop_names:
            result_left.append({'name':propname,'value':value_left})
        if propname in cmpdata_r_prop_names:
            result_right.append({'name':propname,'value':value_right})
    return result_left, result_right


def finddiff_values_text_formatsidebyside( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l):
        cmpdata_l = ''
    if is_empty(cmpdata_r):
        cmpdata_r = ''
    result_left = cmpdata_l
    result_right = cmpdata_r
    if cmpdata_l==cmpdata_r:
        result_left = as_segment_context(cmpdata_l)
        result_right = as_segment_context(cmpdata_r)
    elif( not is_empty(cmpdata_l) and is_empty(cmpdata_r) ):
        result_left = as_segment_change(cmpdata_l,op='removed')
        result_right = ''
    elif( is_empty(cmpdata_l) and not is_empty(cmpdata_r) ):
        result_left = ''
        result_right = as_segment_change(cmpdata_r,op='added')
    else:
        cmpdata_l_into_lines = [ ('' if linenumber==0 else '\n') + (line if len(line)>0 else ' ') for linenumber,line in enumerate(text_split_lines(cmpdata_l)) ]
        cmpdata_r_into_lines = [ ('' if linenumber==0 else '\n') + (line if len(line)>0 else ' ') for linenumber,line in enumerate(text_split_lines(cmpdata_r)) ]
        diff_data = SequenceMatcher(None,cmpdata_l_into_lines,cmpdata_r_into_lines).get_opcodes()
        # TODO: stop working through these proxies DiffItemXxx - I think this is unnecessary, we can work with SequenceMatcher results directly (logged as issue #10)
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
        result_left = {'parts':[]}
        result_right = {'parts':[]}
        for linenumber,part in enumerate(diff_data_l_and_r_by_lines):
            # if linenumber>0:
            #     result_left['parts'].append( '\n' )
            #     result_right['parts'].append( '\n' )
            cmpdata_l_into_pieces = text_split_words(part['l'])
            cmpdata_r_into_pieces = text_split_words(part['r'])
            # TODO: stop working through these proxies DiffItemXxx - I think this is unnecessary, we can work with SequenceMatcher results directly (logged as issue #10)
            diff_data = as_diff_items_concatenated( SequenceMatcher(None,cmpdata_l_into_pieces,cmpdata_r_into_pieces).get_opcodes(), cmpdata_l_into_pieces, cmpdata_r_into_pieces )
            for part in diff_data:
                if part.flag=='keep':
                    result_left['parts'].append(as_segment_context(part.line))
                    result_right['parts'].append(as_segment_context(part.line))
                elif part.flag=='insert':
                    txt_lines = part.line.split('\n')
                    result_left['parts'].append( as_segment_change('\n '.join('' for p in txt_lines),op='added') )
                    result_right['parts'].append( as_segment_change('\n'.join((p if len(p)>0 else ' ') for p in txt_lines),op='added') )
                elif part.flag=='remove':
                    txt_lines = part.line.split('\n')
                    result_left['parts'].append( as_segment_change('\n'.join((p if len(p)>0 else ' ') for p in txt_lines),op='removed') )
                    result_right['parts'].append( as_segment_change('\n '.join('' for p in txt_lines),op='removed') )
                # const_test_l_before = len(re.findall(r'\n',result_left))
                # const_test_r_before = len(re.findall(r'\n',result_right))
                # if const_test_l_before!=const_test_r_before:
                #     # assert line break counts
                # print('linebreaks: {nl} (left), {nr} (right), processing part: {p}'.format(nl=const_test_l_before,nr=const_test_r_before,p=part.line))
        # if result_left['parts'][-1]=='\n':
        #     result_left['parts'] = result_left['parts'][:-1]
        # else:
        #     raise Exception('last part should be \\n, as per my understanding, please check')
        # if result_right['parts'][-1]=='\n':
        #     result_right['parts'] = result_right['parts'][:-1]
        # else:
        #     raise Exception('last part should be \\n, as per my understanding, please check')
    return result_left, result_right

def finddiff_values_list_formatsidebyside( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l):
        cmpdata_l = []
    if is_empty(cmpdata_r):
        cmpdata_r = []
    cmpdata_l_hashed = [(detect_diffsegment_type_noncompulsory(v),f'{v}') for v in cmpdata_l]
    cmpdata_r_hashed = [(detect_diffsegment_type_noncompulsory(v),f'{v}') for v in cmpdata_r]
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
                result_l.append(as_segment_context(item))
                result_r.append(as_segment_context(item))
            elif tag == 'replace':
                result_l.append(as_segment_change(item_l,op='removed') if not is_segment_context(item_l) else item_l)
                result_r.append(as_segment_change(item_r,op='added') if not is_segment_context(item_r) else item_r)
            elif tag == 'insert':
                result_r.append(as_segment_change(item_r,op='added') if not is_segment_context(item_r) else item_r)
            elif tag == 'delete':
                result_l.append(as_segment_change(item_l,op='removed') if not is_segment_context(item_l) else item_l)
    return result_l, result_r

def finddiff_values_segment_formatsidebyside( cmpdata_l, cmpdata_r ):
    # clean inputs
    if is_empty(cmpdata_l):
        cmpdata_l = {}
    if is_empty(cmpdata_r):
        cmpdata_r = {}
    # verify roles (aka "diff segment types")
    role_left = cmpdata_l.get('role',None)
    role_right = cmpdata_r.get('role',None)
    # cast to same denominator, of on is blank/missing and the other indicates something -> make both point to that same something
    if is_empty(role_left) and is_empty(cmpdata_l) and not is_empty(role_right):
        role_left = role_right
    if is_empty(role_right) and is_empty(cmpdata_r) and not is_empty(role_left):
        role_right = role_left
    if not ( (role_left==role_right) or (is_empty(role_left) and is_empty(role_right)) ):
        # if roles are different, don't compare -> instead, treat it as "replaced" - first compared to blank and a separate blank compared to second
        # eres
        # # if (role_left=='context' and not is_empty(cmpdata_l)) or (role_right=='context' and not is_empty(cmpdata_r)):
        # #     pass
        # # chunk_removed_left, chunk_removed_right = finddiff_values_general_formatsidebyside(cmpdata_l,{'role':role_left})
        # # chunk_removed_left = as_segment_change(chunk_removed_left,op='removed')
        # # chunk_removed_right = as_segment_change(chunk_removed_right,op='removed')
        # # chunk_added_left, chunk_added_right = finddiff_values_general_formatsidebyside({'role':role_right},cmpdata_r)
        # # chunk_added_left = as_segment_change(chunk_added_left,op='added')
        # # chunk_added_right = as_segment_change(chunk_added_right,op='added')
        # # return [chunk_removed_left,chunk_added_left], [chunk_removed_right,chunk_added_right]
        return finddiff_values_list_formatsidebyside( [cmpdata_l,None], [None,cmpdata_r] )
    elif role_left=='context' and role_right=='context':
        # or, both roles are "context" -> then, effectively do not not run diff
        return as_segment_context(cmpdata_l), as_segment_context(cmpdata_r)
    
    # work, find final generated chunks
    result_l = {'role':role_left}
    result_r = {'role':role_right}
    # cast to same structure
    if 'parts' in cmpdata_l or 'parts' in cmpdata_r:
        payload_l = cmpdata_l['parts'] if 'parts' in cmpdata_l else as_format(cmpdata_l['text'],detect_format(cmpdata_l['text']),'(list)') if 'text' in cmpdata_l else None
        payload_r = cmpdata_r['parts'] if 'parts' in cmpdata_r else as_format(cmpdata_r['text'],detect_format(cmpdata_r['text']),'(list)') if 'text' in cmpdata_r else None
        diff_l, diff_r = finddiff_values_general_formatsidebyside( payload_l, payload_r )
        result_l['parts'] = diff_l
        result_r['parts'] = diff_r
    else:
        payload_l = cmpdata_l['text'] if 'text' in cmpdata_l else None
        payload_r = cmpdata_r['text'] if 'text' in cmpdata_r else None
        diff_l, diff_r = finddiff_values_general_formatsidebyside( payload_l, payload_r )
        result_l['text'] = diff_l
        result_r['text'] = diff_r

    return result_l,result_r

def finddiff_values_dict_formatsidebyside( cmpdata_l, cmpdata_r ):
    # clean inputs
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
        cmpdata_l_format = detect_format(cmpdata_l)
        cmpdata_r_format = detect_format(cmpdata_r)
        common_format = find_common_format_denominator_with_fallback_str(cmpdata_l_format,cmpdata_r_format)
        return as_format(None,'(none)',common_format),as_format(None,'(none)',common_format)
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
                return finddiff_values_text_formatsidebyside( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='(list)':
                return finddiff_values_list_formatsidebyside( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='(segment)':
                # cmpdata_l = normalize_input_relocate_diff_markers(cmpdata_l)
                # cmpdata_r = normalize_input_relocate_diff_markers(cmpdata_r)
                return finddiff_values_segment_formatsidebyside( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='(dict)':
                # cmpdata_l = normalize_input_relocate_diff_markers(cmpdata_l)
                # cmpdata_r = normalize_input_relocate_diff_markers(cmpdata_r)
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
    result = []
    cmpdata_l_asdict = { record['name']: record['value'] for record in cmpdata_l }
    cmpdata_r_asdict = { record['name']: record['value'] for record in cmpdata_r }
    for propname in prop_names_list_combined:
        value_left = cmpdata_l_asdict[propname] if propname in cmpdata_l_asdict else ''
        value_right = cmpdata_r_asdict[propname] if propname in cmpdata_r_asdict else ''
        result.append({'name':propname,'value':finddiff_values_general_formatcombined(value_left,value_right)})
    return result

def finddiff_values_text_formatcombined( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l):
        cmpdata_l = ''
    if is_empty(cmpdata_r):
        cmpdata_r = ''
    result = {'parts':[]}
    if cmpdata_l==cmpdata_r:
        result = as_segment_context(cmpdata_l)
    elif(not is_empty(cmpdata_l) and is_empty(cmpdata_r) ):
        result = as_segment_change(cmpdata_l,op='removed')
    elif( is_empty(cmpdata_l) and not is_empty(cmpdata_r) ):
        result = as_segment_change(cmpdata_r,op='added')
    else:
        cmpdata_l_into_lines = [ ('' if linenumber==0 else '\n') + (line if len(line)>0 else ' ') for linenumber,line in enumerate(text_split_lines(cmpdata_l)) ]
        cmpdata_r_into_lines = [ ('' if linenumber==0 else '\n') + (line if len(line)>0 else ' ') for linenumber,line in enumerate(text_split_lines(cmpdata_r)) ]
        diff_data = SequenceMatcher(None,cmpdata_l_into_lines,cmpdata_r_into_lines).get_opcodes()
        # TODO: stop working through these proxies DiffItemXxx - I think this is unnecessary, we can work with SequenceMatcher results directly (logged as issue #10)
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
        result = {'parts':[]}
        for linenumber,part in enumerate(diff_data_l_and_r_by_lines):
            # if linenumber>0:
            #     result['parts'].append( '\n' )
            cmpdata_l_into_pieces = text_split_words(part['l'])
            cmpdata_r_into_pieces = text_split_words(part['r'])
            # TODO: stop working through these proxies DiffItemXxx - I think this is unnecessary, we can work with SequenceMatcher results directly (logged as issue #10)
            diff_data = as_diff_items_concatenated( SequenceMatcher(None,cmpdata_l_into_pieces,cmpdata_r_into_pieces).get_opcodes(), cmpdata_l_into_pieces, cmpdata_r_into_pieces )
            for part in diff_data:
                if part.flag=='keep':
                    result['parts'].append(as_segment_context(part.line))
                elif part.flag=='insert':
                    result['parts'].append(as_segment_change(part.line,op='added'))
                elif part.flag=='remove':
                    result['parts'].append(as_segment_change(part.line,op='removed'))
    return result

def finddiff_values_list_formatcombined( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l):
        cmpdata_l = []
    if is_empty(cmpdata_r):
        cmpdata_r = []
    cmpdata_l_hashed = [(detect_diffsegment_type_noncompulsory(v),f'{v}') for v in cmpdata_l]
    cmpdata_r_hashed = [(detect_diffsegment_type_noncompulsory(v),f'{v}') for v in cmpdata_r]
    # list_combined = diff_make_combined_list( cmpdata_l_hashed, cmpdata_r_hashed )
    sm = SequenceMatcher( None,cmpdata_l_hashed, cmpdata_r_hashed )
    result = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        items_l = cmpdata_l[i1:i2]
        items_r = cmpdata_r[j1:j2]
        list_combined = list(zip_longest(items_l, items_r))
        for item_l, item_r in list_combined:
            item = finddiff_values_general_formatcombined( item_l, item_r )
            # if tag == 'equal':
            #     result.append(item)
            # elif tag == 'replace':
            #     result.append(as_segment_change(item_l,op='removed'))
            #     result.append(as_segment_change(item_r,op='added'))
            # elif tag == 'insert':
            #     result.append(as_segment_change(item_r,op='added'))
            # elif tag == 'delete':
            #     result.append(as_segment_change(item_l,op='removed'))
            result.append(item)
    return result

def finddiff_values_segment_formatcombined( cmpdata_l, cmpdata_r ):
    # clean inputs
    if is_empty(cmpdata_l):
        cmpdata_l = {}
    if is_empty(cmpdata_r):
        cmpdata_r = {}
    # verify roles (aka "diff segment types")
    role_left = cmpdata_l.get('role',None)
    role_right = cmpdata_r.get('role',None)
    # cast to same denominator, of on is blank/missing and the other indicates something -> make both point to that same something
    if is_empty(role_left) and is_empty(cmpdata_l) and not is_empty(role_right):
        role_left = role_right
    if is_empty(role_right) and is_empty(cmpdata_r) and not is_empty(role_left):
        role_right = role_left
    if not ( (role_left==role_right) or (is_empty(role_left) and is_empty(role_right)) ):
        # if roles are different, don't compare -> instead, treat it as "replaced" - first compared to blank and a separate blank compared to second
        # return [
        #     as_segment_change(finddiff_values_general_formatcombined(cmpdata_l,{'role':role_left}),op='removed'),
        #     as_segment_change(finddiff_values_general_formatcombined({'role':role_right},cmpdata_r),op='added'),
        # ]
        return finddiff_values_list_formatcombined([cmpdata_l,None],[None,cmpdata_r])
    elif role_left=='context' and role_right=='context':
        # or, both roles are "context" -> then, effectively do not not run diff
        return as_segment_context(finddiff_values_general_formatsimple(cmpdata_l,cmpdata_r))
    
    # work, find final generated chunks
    assert role_left==role_right, 'Khmmm, roles should be the same at this point; please look'
    result = {'role':role_left}
    # cast to same structure
    if 'parts' in cmpdata_l or 'parts' in cmpdata_r:
        payload_l = cmpdata_l['parts'] if 'parts' in cmpdata_l else as_format(cmpdata_l['text'],detect_format(cmpdata_l['text']),'(list)') if 'text' in cmpdata_l else None
        payload_r = cmpdata_r['parts'] if 'parts' in cmpdata_r else as_format(cmpdata_r['text'],detect_format(cmpdata_r['text']),'(list)') if 'text' in cmpdata_r else None
        diff = finddiff_values_general_formatcombined( payload_l, payload_r )
        result['parts'] = diff
    else:
        payload_l = cmpdata_l['text'] if 'text' in cmpdata_l else None
        payload_r = cmpdata_r['text'] if 'text' in cmpdata_r else None
        diff = finddiff_values_general_formatcombined( payload_l, payload_r )
        result['text'] = diff

    return result

def finddiff_values_dict_formatcombined( cmpdata_l, cmpdata_r ):
    # clean inputs
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
        cmpdata_l_format = detect_format(cmpdata_l)
        cmpdata_r_format = detect_format(cmpdata_r)
        common_format = find_common_format_denominator_with_fallback_str(cmpdata_l_format,cmpdata_r_format)
        return as_format(None,'(none)',common_format)
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
            elif cmpdata_l_format=='(segment)':
                # cmpdata_l = normalize_input_relocate_diff_markers(cmpdata_l)
                # cmpdata_r = normalize_input_relocate_diff_markers(cmpdata_r)
                return finddiff_values_segment_formatcombined( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='(dict)':
                return finddiff_values_dict_formatcombined( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='(propertylist)':
                return finddiff_values_propertylist_formatcombined( cmpdata_l, cmpdata_r )
            else:
                return finddiff_values_general_formatcombined( '{f}'.format(f=cmpdata_l), '{f}'.format(f=cmpdata_r) )
        else:
            return finddiff_values_general_formatcombined( '{f}'.format(f=cmpdata_l), '{f}'.format(f=cmpdata_r) )




def finddiff_values_propertylist_formatsimple( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l):
        cmpdata_l = []
    if is_empty(cmpdata_r):
        cmpdata_r = []
    cmpdata_l_prop_names = [ prop['name'] for prop in cmpdata_l ]
    cmpdata_r_prop_names = [ prop['name'] for prop in cmpdata_r ]
    prop_names_list_combined = diff_make_combined_list(cmpdata_l_prop_names,cmpdata_r_prop_names)
    result = []
    cmpdata_l_asdict = { record['name']: record['value'] for record in cmpdata_l }
    cmpdata_r_asdict = { record['name']: record['value'] for record in cmpdata_r }
    for propname in prop_names_list_combined:
        value_left = cmpdata_l_asdict[propname] if propname in cmpdata_l_asdict else ''
        value_right = cmpdata_r_asdict[propname] if propname in cmpdata_r_asdict else ''
        result.append({'name':propname,'value':finddiff_values_general_formatsimple(value_left,value_right)})
    return result

def finddiff_values_text_formatsimple( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l):
        cmpdata_l = ''
    if is_empty(cmpdata_r):
        cmpdata_r = ''
    result = {'parts':[]}
    if cmpdata_l==cmpdata_r:
        result = cmpdata_l
    elif( not is_empty(cmpdata_l) and is_empty(cmpdata_r) ):
        result = cmpdata_l
    elif( is_empty(cmpdata_l) and not is_empty(cmpdata_r) ):
        result = cmpdata_r
    else:
        result = f'Left: {cmpdata_l}, Right: {cmpdata_r}'
    return result

def finddiff_values_list_formatsimple( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l):
        cmpdata_l = []
    if is_empty(cmpdata_r):
        cmpdata_r = []
    cmpdata_l_hashed = [(detect_diffsegment_type_noncompulsory(v),f'{v}') for v in cmpdata_l]
    cmpdata_r_hashed = [(detect_diffsegment_type_noncompulsory(v),f'{v}') for v in cmpdata_r]
    # list_combined = diff_make_combined_list( cmpdata_l_hashed, cmpdata_r_hashed )
    sm = SequenceMatcher( None,cmpdata_l_hashed, cmpdata_r_hashed )
    result = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        items_l = cmpdata_l[i1:i2]
        items_r = cmpdata_r[j1:j2]
        list_combined = list(zip_longest(items_l, items_r))
        for item_l, item_r in list_combined:
            item = finddiff_values_general_formatsimple( item_l, item_r )
            result.append(item)
    return result

def finddiff_values_segment_formatsimple( cmpdata_l, cmpdata_r ):
    return finddiff_values_dict_formatsimple( cmpdata_l, cmpdata_r )

def finddiff_values_dict_formatsimple( cmpdata_l, cmpdata_r ):
    # clean inputs
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
        value_resulting = finddiff_values_general_formatsimple( value_left, value_right )
        result[prop] = value_resulting
    return result


def finddiff_values_general_formatsimple( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l) and is_empty(cmpdata_r):
        cmpdata_l_format = detect_format(cmpdata_l)
        cmpdata_r_format = detect_format(cmpdata_r)
        common_format = find_common_format_denominator_with_fallback_str(cmpdata_l_format,cmpdata_r_format)
        return as_format(None,'(none)',common_format)
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
                return finddiff_values_text_formatsimple( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='(list)':
                return finddiff_values_list_formatsimple( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='(segment)':
                # cmpdata_l = normalize_input_relocate_diff_markers(cmpdata_l)
                # cmpdata_r = normalize_input_relocate_diff_markers(cmpdata_r)
                return finddiff_values_segment_formatsimple( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='(dict)':
                return finddiff_values_dict_formatsimple( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='(propertylist)':
                return finddiff_values_propertylist_formatsimple( cmpdata_l, cmpdata_r )
            else:
                return finddiff_values_general_formatsimple( '{f}'.format(f=cmpdata_l), '{f}'.format(f=cmpdata_r) )
        else:
            return finddiff_values_general_formatsimple( '{f}'.format(f=cmpdata_l), '{f}'.format(f=cmpdata_r) )



