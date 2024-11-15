

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




def splitwords(s):
    return re.sub(r'((?:\w+)|(?:\r?\n)|(?:\s+))',lambda m:'{delimiter}{preserve}{delimiter}'.format(preserve=m[1],delimiter='<<MDMAPSPLIT>>'),s).split('<<MDMAPSPLIT>>')


# temporary repeating similar definitions from diff.py so that I can combine rows and it looks similar
@dataclass(frozen=True)
class DiffItemKeep:
    line: str
    flag = 'keep'
    def __str__(self):
        return '{flag}: {line}'.format(flag=self.flag,line=self.line)
@dataclass(frozen=True)
class DiffItemInsert:
    line: str
    flag = 'insert'
    def __str__(self):
        return 'insert: {line}'.format(flag=self.flag,line=self.line)
@dataclass(frozen=True)
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


def diff_row_names_respecting_groups(rows_l,rows_r):
    # TODO: debug
    if( ( (len(rows_l)>1) and (rows_l[0]!='')) or ( (len(rows_r)>1) and (rows_r[0]!='') ) ):
        print('wrong comparing rows_l and rows_r ("{aaa}..." vs "{bbb}...")'.format(aaa=', '.join(rows_l[:4]),bbb=', '.join(rows_r[:4])))
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
            matches = re.match(r'^(.*?)\.(.*)$',row if '.' in row else '{parent}.{field}'.format(parent=row,field=''))
            row_group = matches[1] # '' is a valid key for dict, we'll have groups_l_defs[''], which means parent item for us, and it should include a list ['']
            row_rest = matches[2]
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
            matches = re.match(r'^(.*?)\.(.*)$',row if '.' in row else '{parent}.{field}'.format(parent=row,field=''))
            row_group = matches[1] # '' is a valid key for dict, we'll have groups_r_defs[''], which means parent item for us, and it should include a list ['']
            row_rest = matches[2]
            if not (row_group in rows_ungrouped_r):
                rows_ungrouped_r.append(row_group)
            if not (row_group in dict.keys(groups_r_defs)) or not groups_r_defs[row_group]:
                groups_r_defs[row_group] = []
            # if row_group!='': # we don't need this condition: even if row_group=='' we still need to have one item in groups_r_defs[row_group]
            groups_r_defs[row_group].append(row_rest)
    grouping_found = False
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
                    diff_within_group_missing_parent_part = diff_row_names_respecting_groups(rows_subgroup_l,rows_subgroup_r)
                    diff_within_group = []
                    item_first_meaning_parent_group = True
                    for diff_item_within_group in diff_within_group_missing_parent_part:
                        item_add = None
                        name_with_parent_part_added = '{parent}.{field}'.format(parent=diff_item.line,field=diff_item_within_group.line) if len(diff_item_within_group.line)>0 else diff_item.line
                        # TODOL debug
                        if( ( item_first_meaning_parent_group and (len(diff_item_within_group.line)>0) ) or ( not item_first_meaning_parent_group and (len(diff_item_within_group.line)==0) )):
                            print('wrong at {aaa}, parent part = {aaap}, field part = {aaaf}, parent flag = {aaapf}, field flag = {aaaff}'.format(
                                aaa=name_with_parent_part_added,
                                aaap=diff_item.line,
                                aaaf=diff_item_within_group.line,
                                aaapf=diff_item.flag,
                                aaaff=diff_item_within_group.flag,
                            ))
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



def combine_similar_records( diff_data ):
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


def diff_values_structural( mdd_l_coldata, mdd_r_coldata ):
    mdd_l_prop_names = [ prop['name'] for prop in mdd_l_coldata ]
    mdd_r_prop_names = [ prop['name'] for prop in mdd_r_coldata ]
    prop_names_list_combined = diff_make_combined_list(mdd_l_prop_names,mdd_r_prop_names)
    result_this_col_left = []
    result_this_col_right = []
    mdd_l_coldata_structural = {}
    for r in mdd_l_coldata:
        mdd_l_coldata_structural[r['name']] = r['value']
    mdd_r_coldata_structural = {}
    for r in mdd_r_coldata:
        mdd_r_coldata_structural[r['name']] = r['value']
    for propname in prop_names_list_combined:
        prop_val_left = ''
        prop_val_right = ''
        if( ( propname in mdd_l_prop_names ) and ( propname in mdd_r_prop_names ) ):
            value_left = mdd_l_coldata_structural[propname]
            value_right = mdd_r_coldata_structural[propname]
            if value_left==value_right:
                prop_val_left = value_left
                prop_val_right = value_right
            elif( (len(value_left)>0) and (len(value_right)==0) ):
                prop_val_left = '<<REMOVED>>' + value_left + '<<ENDREMOVED>>'
                prop_val_right = ''
            elif( (len(value_left)==0) and (len(value_right)>0) ):
                prop_val_left = ''
                prop_val_right = '<<ADDED>>' + value_right + '<<ENDADDED>>'
            else:
                def splitwords(s):
                    return re.sub(r'((?:\w+)|(?:\r?\n)|(?:\s+))',lambda m:'{delimiter}{preserve}{delimiter}'.format(preserve=m[1],delimiter='<<MDMAPSPLIT>>'),s).split('<<MDMAPSPLIT>>')
                value_left = splitwords(value_left)
                value_right = splitwords(value_right)
                diff_data = Myers.to_records(Myers.diff(value_left,value_right),value_left,value_right)
                diff_data = combine_similar_records( diff_data )
                for part in diff_data:
                    if part.flag=='keep':
                        prop_val_left = prop_val_left + part.line
                        prop_val_right = prop_val_right + part.line
                    elif part.flag=='insert':
                        prop_val_right = prop_val_right + '<<ADDED>>' + part.line + '<<ENDADDED>>'
                    elif part.flag=='remove':
                        prop_val_left = prop_val_left + '<<REMOVED>>' + part.line + '<<ENDREMOVED>>'
        elif( propname in mdd_l_prop_names ):
            value_left = mdd_l_coldata_structural[propname]
            prop_val_left = prop_val_left + '<<REMOVED>>' + value_left + '<<ENDREMOVED>>'
        elif( propname in mdd_r_prop_names ):
            value_right = mdd_r_coldata_structural[propname]
            prop_val_right = prop_val_right + '<<ADDED>>' + value_right + '<<ENDADDED>>'
        if propname in mdd_l_prop_names:
            result_this_col_left.append({'name':propname,'value':prop_val_left})
        if propname in mdd_r_prop_names:
            result_this_col_right.append({'name':propname,'value':prop_val_right})
    return result_this_col_left, result_this_col_right


def diff_values_text( mdd_l_coldata, mdd_r_coldata ):                            # TODO: performance issues when finding diff in routing
    # TODO: performance issues when finding diff in routing
    result_this_col_left = mdd_l_coldata
    result_this_col_right = mdd_r_coldata
    if mdd_l_coldata==mdd_r_coldata:
        result_this_col_left = mdd_l_coldata
        result_this_col_right = mdd_r_coldata
    elif( (len(mdd_l_coldata)>0) and (len(mdd_r_coldata)==0) ):
        result_this_col_left = '<<REMOVED>>' + mdd_l_coldata + '<<ENDREMOVED>>'
        result_this_col_right = ''
    elif( (len(mdd_l_coldata)==0) and (len(mdd_r_coldata)>0) ):
        result_this_col_left = ''
        result_this_col_right = '<<ADDED>>' + mdd_r_coldata + '<<ENDADDED>>'
    else:
        mdd_l_coldata = splitwords(mdd_l_coldata)
        mdd_r_coldata = splitwords(mdd_r_coldata)
        diff_data = Myers.to_records(Myers.diff(mdd_l_coldata,mdd_r_coldata),mdd_l_coldata,mdd_r_coldata)
        diff_data = combine_similar_records(diff_data)
        result_this_col_left = ''
        result_this_col_right = ''
        for part in diff_data:
            if part.flag=='keep':
                result_this_col_left = result_this_col_left + part.line
                result_this_col_right = result_this_col_right + part.line
            elif part.flag=='insert':
                text = '' + part.line + ''
                text_lines = re.split(r'\n',text)
                result_this_col_left = result_this_col_left + '\n'.join( ' ' for piece in text_lines )
                result_this_col_right = result_this_col_right + '\n'.join( '<<ADDED>>{a}<<ENDADDED>>'.format(a=piece) for piece in text_lines )
            elif part.flag=='remove':
                text = '' + part.line + ''
                text_lines = re.split(r'\n',text)
                result_this_col_left = result_this_col_left + '\n'.join( '<<REMOVED>>{a}<<ENDREMOVED>>'.format(a=piece) for piece in text_lines )
                result_this_col_right = result_this_col_right + '\n'.join( ' ' for piece in text_lines )
            # const_test_l_before = len(re.findall(r'\n',result_this_col_left))
            # const_test_r_before = len(re.findall(r'\n',result_this_col_right))
            # if const_test_l_before!=const_test_r_before:
            #     pdb.set_trace() # TODO:
            # print('linebreaks: {nl} (left), {nr} (right), processing part: {p}'.format(nl=const_test_l_before,nr=const_test_r_before,p=part.line))
    return result_this_col_left, result_this_col_right
