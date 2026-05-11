


# Aahhhh super ugly sorry
# But, at least, I have it separated



diff_on_diff_diffflag_relabel = {
    '(keep)': '(exists in both left and right)',
    '(removed)': '(only in left)',
    '(added)': '(only in right)',
    '(moved from here)': '(exists in both but position is different)',
    '(moved here)': '(exists in both but position is different)',
}




def make_diffflag_text(exists_in_left,exists_in_right,row_list_status,config = None):
    config = config or {}
    is_diff_on_diff = 'input_is_diff' in config and config['input_is_diff']
    is_ordered = 'config_row_diff_ordered' in config and config['config_row_diff_ordered']
    flag = '???'
    if row_list_status == 'keep':
        flag = '(keep)'
    elif( (exists_in_left) and (exists_in_right) ):
        if is_ordered:
            if row_list_status == 'remove':
                flag = '(moved from here)'
            elif row_list_status == 'insert':
                flag = '(moved here)'
            else:
                raise Exception('Please check diff flag!!!')
        else:
            flag = '(keep)'
    elif( exists_in_left ):
        flag = '(removed)'
    elif( exists_in_right ):
        flag = '(added)'
    if is_diff_on_diff:
        flag = diff_on_diff_diffflag_relabel.get(flag,flag)
    return flag
