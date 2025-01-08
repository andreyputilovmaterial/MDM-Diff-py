

import re

# from collections import namedtuple
from dataclasses import dataclass





if __name__ == '__main__':
    # run as a program
    from lib.difflib.diff import Myers
elif '.' in __name__:
    # package
    from .lib.difflib.diff import Myers
else:
    # included with no parent package
    from lib.difflib.diff import Myers




def is_empty(s):
    if s==0:
        return False
    else:
        return not s


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



# temporary repeating similar definitions from diff.py so that I can combine rows and it looks similar
@dataclass(frozen=False)
class DiffItemKeep:
    line: str
    flag = 'keep'
    def __str__(self):
        return '{flag}: {line}'.format(flag=self.flag,line=self.line)

@dataclass(frozen=False)
class DiffItemInsert:
    line: str
    flag = 'insert'
    def __str__(self):
        return 'insert: {line}'.format(flag=self.flag,line=self.line)

@dataclass(frozen=False)
class DiffItemRemove:
    line: str
    flag = 'remove'
    def __str__(self):
        return 'remove: {line}'.format(flag=self.flag,line=self.line)





def diff_make_combined_list(list_l,list_r):
    results = []
    for item in Myers.to_records(Myers.diff(list_l,list_r),list_l,list_r):
        if not (item.line in results):
            results.append(item.line)
    return results

def diff_raw(list_l,list_r):
    # just a wrapper
    return Myers.diff(list_l,list_r)



def did_contents_change_deep_inspect(data):
    if isinstance(data,str):
        if '<<ADDED>>' in data:
            return True
        if '<<REMOVED>>' in data:
            return True
        return False
    elif isinstance(data,list):
        result = False
        for slice in data:
            result = result or did_contents_change_deep_inspect(slice)
        return result
    elif isinstance(data,dict) and 'text' in data:
        if 'role' in data:
            if re.match(r'^\s*?(?:role-)?(?:added|removed).*?',data['role'],flags=re.I):
                return True
        return did_contents_change_deep_inspect(data['text'])
    elif isinstance(data,dict) and 'parts' in data:
        return did_contents_change_deep_inspect(data['parts'])
    elif isinstance(data,dict) and 'name' in data and 'value' in data:
        return did_contents_change_deep_inspect(data['value'])
    else:
        return did_contents_change_deep_inspect('{f}'.format(f=data))




class MDMDiffWrappersGroupingMissingParentException(Exception):
    """Diff: diff item names with groupings: every group must include a parent element"""
def finddiff_row_names_respecting_groups(rows_l,rows_r,delimiter,level=None):
    try:
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
                raise MDMDiffWrappersGroupingMissingParentException('diff item names with groupings: every group must include a parent element. For example, if there is "QCData.Flags.Categories...", there should be a parent "QCData.Flags", and its parent "QCData", and its parent "" (a root element, just an empty string)')
        for g in dict.keys(groups_l_defs):
            grouping_found = grouping_found or (len(groups_l_defs[g])>1)
        for g in dict.keys(groups_r_defs):
            grouping_found = grouping_found or (len(groups_r_defs[g])>1)
        diff_results = Myers.to_records(Myers.diff(rows_ungrouped_l,rows_ungrouped_r),rows_ungrouped_l,rows_ungrouped_r)
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
                        diff_within_group_missing_parent_part = finddiff_row_names_respecting_groups(rows_subgroup_l,rows_subgroup_r,delimiter,level=diff_item.line)
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



def process_make_name_prop_unique(file_l_sectiondata,file_r_sectiondata,columns_list_check):
    name_col_backup_name = 'name_backup'
    if name_col_backup_name in columns_list_check:
        iii = 0
        while name_col_backup_name in columns_list_check:
            name_col_backup_name = 'name_backup_{ver}'.format(ver=iii)
            iii = iii + 1
    for row in file_l_sectiondata:
        row[name_col_backup_name] = row['name']
    for row in file_r_sectiondata:
        row[name_col_backup_name] = row['name']
    missing_row_name_holder = '???'
    all_row_names = [] + [ ( item['name'] if 'name' in item else '' ) for item in file_l_sectiondata ] + [ ( item['name'] if 'name' in item else '' ) for item in file_r_sectiondata ]
    if missing_row_name_holder in all_row_names:
        iii = 0
        while missing_row_name_holder in all_row_names:
            missing_row_name_holder = '??? ({ver})'.format(ver=iii)
            iii = iii + 1
    rows_l = [ ( item['name'] if 'name' in item else missing_row_name_holder ) for item in file_l_sectiondata ]
    rows_r = [ ( item['name'] if 'name' in item else missing_row_name_holder ) for item in file_r_sectiondata ]
    diff_temp = diff_raw(rows_l,rows_r)
    # add a dummy element for trailing part
    diff_temp.append({
        'lhs': {
            'at': len(rows_l),
            'add': 0,
            'del': 0
        },
        'rhs': {
            'at': len(rows_r),
            'add': 0,
            'del': 0
        }
    })
    # go
    last_index = 0
    names_used = []
    # first we separately process all "keep", and then we'll iterate again and process all "added" and "removed"
    # the reason is that sometimes we are adding " (2)" to a "keep" item which does not make sense
    # so we'll populate all "keep" items first
    for diff_entry in diff_temp:
        part_l_keep_start = last_index
        part_l_keep_end = diff_entry['lhs']['at']
        part_r_keep_shift = diff_entry['rhs']['at'] - diff_entry['lhs']['at']
        part_l_del_start = diff_entry['lhs']['at']
        part_l_del_end = diff_entry['lhs']['at'] + diff_entry['lhs']['del']
        part_r_add_start = diff_entry['rhs']['at']
        part_r_add_end = diff_entry['rhs']['at'] + diff_entry['rhs']['add']
        last_index = diff_entry['lhs']['at'] + diff_entry['lhs']['del']
        for i in range(part_l_keep_start,part_l_keep_end):
            # no change - names are good
            name_orig = file_l_sectiondata[i]['name']
            name_upd = name_orig
            if name_upd in names_used:
                iii = 2
                while name_upd in names_used:
                    name_upd = '{part_orig} ({part_increment})'.format(part_orig=name_orig,part_increment=iii)
                    while name_upd in all_row_names:
                        name_upd = '{part_orig} ({part_increment})'.format(part_orig=name_orig,part_increment=iii)
                        iii = iii + 1
                    iii = iii + 1
            names_used.append(name_upd)
            file_l_sectiondata[i]['name'] = name_upd
            file_r_sectiondata[i+part_r_keep_shift]['name'] = name_upd
    for diff_entry in diff_temp:
        part_l_keep_start = last_index
        part_l_keep_end = diff_entry['lhs']['at']
        part_r_keep_shift = diff_entry['rhs']['at'] - diff_entry['lhs']['at']
        part_l_del_start = diff_entry['lhs']['at']
        part_l_del_end = diff_entry['lhs']['at'] + diff_entry['lhs']['del']
        part_r_add_start = diff_entry['rhs']['at']
        part_r_add_end = diff_entry['rhs']['at'] + diff_entry['rhs']['add']
        last_index = diff_entry['lhs']['at'] + diff_entry['lhs']['del']
        for i in range(part_l_del_start,part_l_del_end):
            # removed
            name_orig = file_l_sectiondata[i]['name']
            name_upd = name_orig
            if name_upd in names_used:
                iii = 2
                while name_upd in names_used:
                    name_upd = '{part_orig} ({part_increment})'.format(part_orig=name_orig,part_increment=iii)
                    while name_upd in all_row_names:
                        name_upd = '{part_orig} ({part_increment})'.format(part_orig=name_orig,part_increment=iii)
                        iii = iii + 1
                    iii = iii + 1
            names_used.append(name_upd)
            file_l_sectiondata[i]['name'] = name_upd
        for i in range(part_r_add_start,part_r_add_end):
            # added
            name_orig = file_r_sectiondata[i]['name']
            name_upd = name_orig
            if name_upd in names_used:
                iii = 2
                while name_upd in names_used:
                    name_upd = '{part_orig} ({part_increment})'.format(part_orig=name_orig,part_increment=iii)
                    while name_upd in all_row_names:
                        name_upd = '{part_orig} ({part_increment})'.format(part_orig=name_orig,part_increment=iii)
                        iii = iii + 1
                    iii = iii + 1
            names_used.append(name_upd)
            file_r_sectiondata[i]['name'] = name_upd
    return file_l_sectiondata, file_r_sectiondata
    


# this is a very common function that I am using
# the diffing fn is designed to return a patch
# but very often I need a list with all items, every item indicated if it was persisted, added, or removed
# so this is converting patch to a list
def diff_combine_similar_records( diff_data ):
    for i in range(len(diff_data)):
        if i>0:
            if (diff_data[i].flag=='keep') and (diff_data[i-1].flag=='keep'):
                diff_data[i] = DiffItemKeep(diff_data[i-1].line+diff_data[i].line)
                diff_data[i-1] = DiffItemKeep('')
            if (diff_data[i].flag=='insert') and (diff_data[i-1].flag=='insert'):
                diff_data[i] = DiffItemInsert(diff_data[i-1].line+diff_data[i].line)
                diff_data[i-1] = DiffItemKeep('')
            if (diff_data[i].flag=='remove') and (diff_data[i-1].flag=='remove'):
                diff_data[i] = DiffItemRemove(diff_data[i-1].line+diff_data[i].line)
                diff_data[i-1] = DiffItemKeep('')
    diff_data = filter(lambda e:(len(e.line)>0),diff_data)
    return diff_data



def check_if_includes_addedremoved_marker(data):
    if is_empty(data):
        return False
    if isinstance(data,list) and ([(True if 'name' in dict.keys(item) else False) for item in data].count(True)==len(data)):
        result = False
        for prop in data:
            result = result or check_if_includes_addedremoved_marker(prop['value'])
        return result
    elif isinstance(data,dict) and ('role' in dict.keys(data)) and re.match(r'^\s*?(?:role-)?(add|remove|change).*?$',data['role'],flags=re.I):
        return True
    elif isinstance(data,dict) and ('parts' in dict.keys(data)):
        result = False
        for part in data['parts']:
            result = result or check_if_includes_addedremoved_marker(part)
        return result
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
    elif ('{fmt}'.format(fmt=data)==data):
        # TODO: drop support of <<ADDED>>, <<REMOVED>> markers
        if ('<<ADDED>>' in '{fmt}'.format(fmt=data)) or ('<<REMOVED>>' in '{fmt}'.format(fmt=data)):
            return True
        return False
    else:
        # raise ValueError('Can\'t handle this type of data: {d}'.format(d=data))
        #return check_if_includes_addedremoved_marker(json.dumps(data))
        return check_if_includes_addedremoved_marker('{d}'.format(d=data))




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
    cmpdata_l_structural = {}
    for r in cmpdata_l:
        cmpdata_l_structural[r['name']] = r['value']
    cmpdata_r_structural = {}
    for r in cmpdata_r:
        cmpdata_r_structural[r['name']] = r['value']
    for propname in prop_names_list_combined:
        prop_val_left = {'parts':[]}
        prop_val_right = {'parts':[]}
        if( ( propname in cmpdata_l_prop_names ) and ( propname in cmpdata_r_prop_names ) ):
            value_left = cmpdata_l_structural[propname]
            value_right = cmpdata_r_structural[propname]
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
            value_left = cmpdata_l_structural[propname]
            prop_val_left = {'text':value_left,'role':'removed'}
        elif( propname in cmpdata_r_prop_names ):
            value_right = cmpdata_r_structural[propname]
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
        diff_data = Myers.diff(cmpdata_l_into_lines,cmpdata_r_into_lines)
        diff_data = Myers.to_records(diff_data,cmpdata_l_into_lines,cmpdata_r_into_lines)
        diff_data = diff_combine_similar_records(diff_data)
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
            diff_data = Myers.to_records(Myers.diff(cmpdata_l_into_pieces,cmpdata_r_into_pieces),cmpdata_l_into_pieces,cmpdata_r_into_pieces)
            diff_data = diff_combine_similar_records(diff_data)
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
    list_combined = diff_make_combined_list( cmpdata_l, cmpdata_r )
    result_l = []
    result_r = []
    for item in list_combined:
        if (item in cmpdata_l) and (item in cmpdata_r):
            result_l.append({'text':item})
            result_r.append({'text':item})
        elif not (item in cmpdata_l) and (item in cmpdata_r):
            result_r.append({'text':item,'role':'added'})
        elif (item in cmpdata_l) and not (item in cmpdata_r):
            result_l.append({'text':item,'role':'removed'})
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
        value_resulting = value_resulting = finddiff_values_general_formatcombined( value_left, value_right )
        if prop in cmpdata_l:
            result_l[prop] = value_resulting
        if prop in cmpdata_r:
            result_r[prop] = value_resulting
    return result_l,result_r

def finddiff_values_general_formatsidebyside( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l) and is_empty(cmpdata_r):
        return '',''
    else:
        def detect_format(val):
            if is_empty(val):
                return 'none'
            elif isinstance(val,list) and len(val)==0:
                return 'none'
            elif isinstance(val,list) and (len([v for v in val if isinstance(v,dict) and 'name' in v])==len(val)):
                return 'propertylist'
            elif isinstance(val,list) and (len([v for v in val if isinstance(v,str)])==len(val)):
                return 'list'
            elif isinstance(val,dict):
                return 'dict'
            elif isinstance(val,str):
                return 'str'
            else:
                return 'unrecognized'
        cmpdata_l_format = detect_format(cmpdata_l)
        cmpdata_r_format = detect_format(cmpdata_r)
        if cmpdata_l_format=='none':
            cmpdata_l_format = cmpdata_r_format
        if cmpdata_r_format=='none':
            cmpdata_r_format = cmpdata_l_format
        if (cmpdata_l_format==cmpdata_r_format):
            if cmpdata_l_format=='str':
                return finddiff_values_text_formatsidebyside( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='list':
                return finddiff_values_list_formatsidebyside( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='dict':
                return finddiff_values_dict_formatsidebyside( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='propertylist':
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
    cmpdata_l_structural = {}
    for r in cmpdata_l:
        cmpdata_l_structural[r['name']] = r['value']
    cmpdata_r_structural = {}
    for r in cmpdata_r:
        cmpdata_r_structural[r['name']] = r['value']
    for propname in prop_names_list_combined:
        value_left = cmpdata_l_structural[propname] if propname in cmpdata_l_structural else ''
        value_right = cmpdata_r_structural[propname] if propname in cmpdata_r_structural else ''
        result_this_col_combined.append({'name':propname,'value':finddiff_values_general_formatcombined(value_left,value_right)})
    return result_this_col_combined

def finddiff_values_text_formatcombined( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l):
        cmpdata_l = ''
    if is_empty(cmpdata_r):
        cmpdata_r = ''
    result_this_col_combined = {'parts':[]}
    if cmpdata_l==cmpdata_r:
        result_this_col_combined = cmpdata_l
    elif( (len(cmpdata_l)>0) and (len(cmpdata_r)==0) ):
        result_this_col_combined = {'parts':[{'text':cmpdata_l,'role':'removed'}]}
    elif( (len(cmpdata_l)==0) and (len(cmpdata_r)>0) ):
        result_this_col_combined = {'parts':[{'text':cmpdata_r,'role':'added'}]}
    else:
        cmpdata_l_into_lines = [ ('' if linenumber==0 else '\n') + (line if len(line)>0 else ' ') for linenumber,line in enumerate(text_split_lines(cmpdata_l)) ]
        cmpdata_r_into_lines = [ ('' if linenumber==0 else '\n') + (line if len(line)>0 else ' ') for linenumber,line in enumerate(text_split_lines(cmpdata_r)) ]
        diff_data = Myers.diff(cmpdata_l_into_lines,cmpdata_r_into_lines)
        diff_data = Myers.to_records(diff_data,cmpdata_l_into_lines,cmpdata_r_into_lines)
        diff_data = diff_combine_similar_records(diff_data)
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
            diff_data = Myers.to_records(Myers.diff(cmpdata_l_into_pieces,cmpdata_r_into_pieces),cmpdata_l_into_pieces,cmpdata_r_into_pieces)
            diff_data = diff_combine_similar_records(diff_data)
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
    list_combined = diff_make_combined_list( cmpdata_l, cmpdata_r )
    result = []
    for item in list_combined:
        if (item in cmpdata_l) and (item in cmpdata_r):
            result.append({'text':item})
        elif not (item in cmpdata_l) and (item in cmpdata_r):
            result.append({'text':item,'role':'added'})
        elif (item in cmpdata_l) and not (item in cmpdata_r):
            result.append({'text':item,'role':'removed'})
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
        value_resulting = value_resulting = finddiff_values_general_formatcombined( value_left, value_right )
        result[prop] = value_resulting
    return result

def finddiff_values_general_formatcombined( cmpdata_l, cmpdata_r ):
    if is_empty(cmpdata_l) and is_empty(cmpdata_r):
        return ''
    else:
        def detect_format(val):
            if is_empty(val):
                return 'none'
            elif isinstance(val,list) and len(val)==0:
                return 'none'
            elif isinstance(val,list) and (len([v for v in val if isinstance(v,dict) and 'name' in v])==len(val)):
                return 'propertylist'
            elif isinstance(val,list) and (len([v for v in val if isinstance(v,str)])==len(val)):
                return 'list'
            elif isinstance(val,dict):
                return 'dict'
            elif isinstance(val,str):
                return 'str'
            else:
                return 'unrecognized'
        cmpdata_l_format = detect_format(cmpdata_l)
        cmpdata_r_format = detect_format(cmpdata_r)
        if cmpdata_l_format=='none':
            cmpdata_l_format = cmpdata_r_format
        if cmpdata_r_format=='none':
            cmpdata_r_format = cmpdata_l_format
        if (cmpdata_l_format==cmpdata_r_format):
            if cmpdata_l_format=='str':
                return finddiff_values_text_formatcombined( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='list':
                return finddiff_values_list_formatcombined( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='dict':
                return finddiff_values_dict_formatcombined( cmpdata_l, cmpdata_r )
            elif cmpdata_l_format=='propertylist':
                return finddiff_values_propertylist_formatcombined( cmpdata_l, cmpdata_r )
            else:
                return finddiff_values_general_formatcombined( '{f}'.format(f=cmpdata_l), '{f}'.format(f=cmpdata_r) )
        else:
            return finddiff_values_general_formatcombined( '{f}'.format(f=cmpdata_l), '{f}'.format(f=cmpdata_r) )

