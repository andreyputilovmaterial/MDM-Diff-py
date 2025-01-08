import re
from datetime import datetime, timezone


import pandas as pd


# this file is used to read excel

# in general way
# first we try to read as lrw
# if can't, we read using funcitons here

# the other possibility when reading excels (that is not mentioned here) is to read it with ms markitdown
# maybe it can be a better option in some cases

# maybe comments here are too extensive, sometimes unnecessary
# but it's nice to have, it's easier to read





# this was used for processing rows in groups
# for example, if there's a group of rows for "Netflix" or "Hulu" stubs, including Base, Likelihood to recommend, or some scale, and these rows are moved - it si processed as a group
# but if fact we are not using grouping when processing excel tabs
# because grouping implies certain structure (as designed in diff script) - every group must have a parent item
# and we don't follow that standard in tabs (we can add a parent empty item but why?)
# but adding group names is still useful so that we correctly identify which group does every row belong to
# for example, if there's a scale, we should know if it's for Disney or Netflix or Hulu
CONFIG_NAME_DELIMITER = ' / '



# I used to trim whitespaces everywhere
# adding trim() fn is not a pythonic way but it follows the same standards I am using elsewhere
def trim(s):
    if s==0:
        return '0'
    if not s:
        return ''
    return '{s}'.format(s=s).strip()



# detects cell content type
# return certain flags - flag if numeric, flag if blank, etc...
# but flags are single-punch: only one value is returned - it can be numeric, OR blank, or ... something else, but not a combination
def detect_cell_type(v):
    if v==0:
        return 'numeric'
    elif not v:
        return 'empty'
    elif trim(v)=='':
        return 'empty'
    else:
        try:
            a = int(v)
            if(a>0 or a<0 or a==0):
                return 'numeric'
            else:
                return 'value'
        except Exception:
            return 'value'



# this fn detects col type for every column within area - if it's blank, if its values are unique, if all cell values are numeric, etc...
def gather_columns_info(df_thissheet):

    blank_rows = []
    rows = [ trim(''.join([trim(s) for s in df_thissheet.iloc[idx,0:]])) for idx in range(0,len(df_thissheet)) ]
    for rownumber,row in enumerate(rows):
        if trim(row)=='':
            blank_rows.append(rownumber)

    columns = []
    for col_index in range(0,len(df_thissheet.columns)):
        is_empty = True
        is_unique = True
        is_numeric = True
        has_missing_values = False
        has_data = False
        prev_values = []
        for rownumber,row_txt in enumerate(df_thissheet.iloc[0:,col_index]):
            if rownumber in blank_rows:
                continue
            row_type = detect_cell_type(row_txt)
            if row_type=='empty':
                has_missing_values = True
                pass
            else:
                is_empty = False
                has_data = True
                if row_type=='value':
                    is_numeric = False
                if row_txt in prev_values:
                    is_unique = False
                prev_values.append(row_txt)
        if is_empty:
            is_unique = False
            is_numeric = False
            has_missing_values = True
        columns.append({
            'is_empty': is_empty,
            'is_numeric': is_numeric,
            'is_unique': is_unique,
            'has_data': has_data,
            'has_missing_values': has_missing_values,
        })
    return columns

def trim_rows(df):
    return df


# helper fn
# we check if we can use the first row as a banner
# it is very common that the first row is banner
# but not always
# the condition is the following: no blank values and no duplicates
def is_valid_banner(row):
    vals_used = []
    is_good = True
    for s in row:
        t = detect_cell_type(s)
        if not (t=='value'):
            is_good = False
        if s in vals_used:
            is_good = False
        vals_used.append(s)
    return is_good


# first we find areas with data on the sheet
# sometimes a sheet includes seveval blocks of data
# even Grant is using it in mapping, painless, flatout, reshape...
def find_data_areas_within_sheet(df_thissheet):
    # chectsheet: get contents of (x,y): df_thissheet.iloc[x,y]

    columns = gather_columns_info(df_thissheet)

    start = 0
    curr = 0
    while True:
        if curr>=len(df_thissheet.columns):
            if curr-1>=start:
                yield trim_rows(df_thissheet[[col for colindex,col in enumerate(df_thissheet.columns) if colindex in range(start,curr)]])
                break
        if columns[curr]['is_empty']:
            if curr-1>=start:
                yield trim_rows(df_thissheet[[col for colindex,col in enumerate(df_thissheet.columns) if colindex in range(start,curr)]])
            start = curr + 1
        curr = curr + 1





# main entry point
def read_excel(filename):

    xls = pd.ExcelFile(filename,engine='openpyxl')

    data = {
        'report_type': 'Excel File',
        'source_file': '{f}'.format(f=filename),
        'report_datetime_utc': '{f}'.format(f=(datetime.now()).astimezone(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),),
        'report_datetime_local': '{f}'.format(f=(datetime.now()).strftime('%Y-%m-%dT%H:%M:%SZ')),
        'report_scheme': {
            'columns': [
                'name',
                # 'label'
            ],
            'column_headers': {
                'name': 'Row unique indentifier',
                # 'label': 'First Column'
            },
            'flags': [ 'data-type:excel' ]
        },
        'source_file_metadata': [],
        'sections': []
    }

    sheet_names = xls.sheet_names
    global_columnid_lookup = {

    }
    column_zero = 'axis(side)' # that's how we call column 0 by default; and row 0 should be called "axis(top)"" then

    # a helper fn to suggest column name that is used as an ID
    # basically we are trying to use cell contents as a name, but we can modify or add something to ensure it's unique
    def get_column_id(col,try_certain_id=None):
        if try_certain_id:
            name_preliminary = try_certain_id
        else:
            name_preliminary = re.sub(r'([^a-zA-Z])',lambda m: '_x{d}_'.format(d=ord(m[1])),re.sub(r'_+$','',re.sub(r'^_+','',re.sub(r'[\s_]+','_','col_{f}'.format(f=col)))),flags=re.I)
        if not (name_preliminary in global_columnid_lookup):
            global_columnid_lookup[name_preliminary] = col
            return name_preliminary
        elif name_preliminary in global_columnid_lookup and col==global_columnid_lookup[name_preliminary]:
            return name_preliminary
        else:
            return get_column_id(col,name_preliminary+'_2')
        



    # print('reading excel: reading whole file')
    # df = xls.parse( sheet_name=None, index_col=None, header=0)

    # this helper fn was used in lrw-type excels (now implemented in a separate file)
    # like the sheet with TOC is meaningless and the sheet with data is meaningful
    # so I still keep this as a place for code so that I can add logic here
    # but in fact I don't know what can be checked if we don't know anything about the excel being read
    # so I just return true
    def is_meaningful_sheet(sheet_name):
        return True

    # ok, go for it and iterate over all sheets with data
    for sheet_name in [ sheet_name for sheet_name in sheet_names if is_meaningful_sheet(sheet_name) ]:

        try:

            print('reading excel: sheet: {sh}'.format(sh=sheet_name))


            resulting_tab_def = {
                'name': sheet_name,
                'columns': ['name'],
                'column_headers': {},
                'content': []
            }
            
            # inspect sheet contents
            data_areas_within_sheet = find_data_areas_within_sheet(xls.parse(sheet_name=sheet_name, index_col=None, header=None).fillna(''))

            # then process every area (yeah such comments are unnecessary)
            for df in data_areas_within_sheet:

                # detect types of columns - which are blank, or contain unique identifiers
                columns_data = gather_columns_info(df)

                # in ID for index col
                idcol = -1
                if len(columns_data)>0 and columns_data[0]['is_unique']:
                    idcol = 0
                if len(columns_data)>1 and columns_data[0]['is_unique'] and columns_data[0]['is_numeric'] and columns_data[1]['is_unique'] and not columns_data[1]['is_numeric']:
                    idcol = 1
                header_index = -1
                if is_valid_banner(df.iloc[0,0:]):
                    header_index = 0
                    for c in range(0,len(df.columns)):
                        columns_data[c]['name'] = df.iloc[0,c]
                else:
                    header_index = -1
                    for c in range(0,len(df.columns)):
                        columns_data[c]['name'] = 'Column #{n}'.format(n=c)
                
                # prep what we store as column names (banner points)
                col_names = [ c['name'] for c in columns_data ]
                col_labels = {}
                for c in col_names:
                    col_labels[c] = c
                    if not (c in data['report_scheme']['columns']):
                        data['report_scheme']['columns'].append(c)
                    if not (c in data['report_scheme']['column_headers']):
                        data['report_scheme']['column_headers'][c] = c
                    if not (c in resulting_tab_def['columns']):
                        resulting_tab_def['columns'].append(c)
                    if not (c in resulting_tab_def['column_headers']):
                        resulting_tab_def['column_headers'][c] = c
                
                # ok, process data!
                for rownumber in range(header_index+1,len(df)):
                    r = df.iloc[rownumber,0:]
                    if len(r)>0:
                        row = {
                            'name': 'Line #{n}'.format(n=rownumber+1 if idcol<0 else r.iat[idcol] )
                        }
                        for c in range(0,len(r)):
                            row[columns_data[c]['name']] = r.iat[c]
                        resulting_tab_def['content'].append(row)
            
            # done!
            data['sections'].append(resulting_tab_def)
                

        except Exception as e:
            print('reading excel: failed when reading sheet "{sn}"'.format(sn=sheet_name))
            raise e
    
    return data



