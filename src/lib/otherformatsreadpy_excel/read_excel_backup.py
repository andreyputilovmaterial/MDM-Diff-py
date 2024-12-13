from pathlib import Path
import re
import argparse
import json
from datetime import datetime, timezone


import pandas as pd
import numpy as np # needed for correct handling of pandas types when converting to json - pandas types are based on numpy





def trim(s):
    if not s:
        return ''
    return '{s}'.format(s=s).strip()





class MDMExcelReadFormatException(Exception):
    """Reading Excel: failed with a given format"""




def special_lrw_read_index_sheet(df_mainpage):
    result = []
    result_metadata = []

    if not ( len( df_mainpage.loc[ df_mainpage[ df_mainpage.columns[0] ].astype('str').str.contains(r'^\s*?Table of Contents\s*?$',regex=True,case=False) ] )>0 ):
        raise MDMExcelReadFormatException
    
    rows = [ df_mainpage.iloc[idx,0] for idx in range(0,len(df_mainpage)) ]
    section_currentlyreading = 'preface'
    print('reading excel: reading table names')
    for rownumber,row in enumerate(rows):
        row_txt = row
        if re.match(r'^\s*?$',row_txt):
            continue
        else:
            if re.match(r'^\s*?Table of Contents\s*?$',row_txt,flags=re.I):
                #section_currentlyreading = 'banner_row'
                section_currentlyreading = 'tables'
                continue
        if (section_currentlyreading=='tables'):
            matches = re.match(r'^\s*?(?:T|Table)\s*?(\d+)\s*?-\s*(.*?)\s*$',row_txt,flags=re.I)
            if not matches:
                raise MDMExcelReadFormatException('reading excel: indexsheet: Reading list of tables, passed beyound "Table of Contents", expecting "Table 1 - ...", found something else, unexpected line = {l}, text = {t}'.format(l=row,t=row_txt))
            tablenum = int(matches[1])
            tabletitle = matches[2]
            result.append({
                'number': tablenum,
                'title': tabletitle,
                'name': tabletitle,
                'columns': ['name'],
                'column_headers': {},
                'content': []
            })
        elif (section_currentlyreading=='preface'):
            if len(trim(row_txt))>0:
                result_metadata.append({'name':'line {d}'.format(d=rownumber),'value':trim(row_txt)})
        else:
            raise AttributeError('reading excel: indexsheet: Reading list of tables, passed beyound "Table of Contents", expecting "Table 1 - ...", found something else, unexpected line = {l}, text = {t}'.format(l=row,t=row_txt))
    
    # check that table names are unique
    table_names_already_used = []
    for section_def in result:
        table_name = section_def['name']
        if table_name in table_names_already_used:
            table_name_override_suggest = None
            table_name_override_counter = 2
            while True:
                table_name_override_suggest = '{keep}{added}'.format(keep=table_name,added=' [Duplicate #] {d}]'.format(d=table_name_override_counter))
                if not(table_name_override_suggest in table_names_already_used):
                    break
                else:
                    table_name_override_counter = table_name_override_counter + 1
            section_def['name'] = table_name_override_suggest
            print('WARNING: duplicate table names: renaming a table to "{tabtitle}"'.format(tabtitle=table_name_override_suggest))
        table_names_already_used.append(table_name)
        
    return result, result_metadata



def add_or_find_section_entry(sections_to_look_for,sheet_name):
    table_defs = sections_to_look_for
    table_defs_matching = [ tab for tab in [ tab for tab in table_defs if 'number' in tab and tab['number']>0 ] if 'T{n}'.format(n=tab['number'])==sheet_name ]
    if len(table_defs_matching)!=1:
        #raise ValueError('reading excel: tab def not found for {n} (we are reading sheet "{n}" but we were not able to grab this table title from index sheet)'.format(n=sheet_name))
        section_def_add = {
            'name': sheet_name,
            'columns': ['name'],
            'column_headers': {},
            'content': []
        }
        sections_to_look_for.append(section_def_add)
        table_defs_matching = [sections_to_look_for[-1]]          
    result = table_defs_matching[0]
    return result





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
    is_detected_known_format = None
    global_columnid_lookup = {

    }
    column_zero = 'axis(side)' # that's how we call column 0 by default; and row 0 should be called "axis(top)"" then
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
        

    if 'IndexSheet' in sheet_names and 'T1' in sheet_names: # lrw format - trying to read TOC (table of contents)
        # lrw format - we are expecting that here, on "IndexSheet", there is a line "Table of Contents", and a list of tables below
        # if there is, we grab table names, and set is_detected_known_format = 'lrw'
        df_mainpage = xls.parse(sheet_name='IndexSheet', index_col=None).fillna(0)
        print('reading excel: reading index sheet')
        try:
            result,result_metadata = special_lrw_read_index_sheet(df_mainpage)
            data['sections'].extend( result )
            data['source_file_metadata'].extend( result_metadata )
            is_detected_known_format = 'lrw'
        except MDMExcelReadFormatException:
            pass



    # print('reading excel: reading whole file')
    # df = xls.parse( sheet_name=None, index_col=None, header=0)

    def is_meaningful_sheet(sheet_name):
        if is_detected_known_format=='lrw':
            return  re.match(r'^\s*?(?:T|Table)\s*?\d+\s*?$',sheet_name,flags=re.I)
        return True

    for sheet_name in [ sheet_name for sheet_name in sheet_names if is_meaningful_sheet(sheet_name) ]:

        try:

            print('reading excel: sheet: {sh}'.format(sh=sheet_name))
            df_thissheet = xls.parse(sheet_name=sheet_name, index_col=None, header=None)

            tab_def = add_or_find_section_entry(sections_to_look_for=data['sections'],sheet_name=sheet_name)
            
            # inspect sheet contents
            # data_areas_within_sheet = recognize_data_areas_within_sheet() # TODO:

            df_thissheet_clean = df_thissheet.fillna('')
            rows = [ {'col_1':trim(df_thissheet_clean.iloc[idx,0]),'col_rest':trim(''.join([trim(s) for s in df_thissheet_clean.iloc[idx,1:]]))} for idx in range(0,len(df_thissheet)) ]
            linenumber = 0
            linenumber_banner_begins = 0
            linenumber_banner_ends = 0
            linenumber_banner_most_informative = 0
            linenumber_data_starts = 0
            linenumber_last = len(rows)-1
            while( (linenumber<=linenumber_last) and (len(rows[linenumber]['col_rest'])==0)):
                linenumber = linenumber + 1
            if linenumber > linenumber_last:
                print('WARNING: read excel: table #{t}: no banner found'.format(t=sheet_name))
                # TODO: actually I'll make it a critical error, I'll stop here
                raise ValueError('WARNING: read excel: table #{t}: no banner found'.format(t=sheet_name))
                continue
            linenumber_banner_begins = linenumber
            # linenumber = linenumber + 1 # ???
            while( (linenumber<=linenumber_last) and (len(rows[linenumber]['col_1'])==0) and (len(rows[linenumber]['col_rest'])>0) ):
                linenumber = linenumber + 1
            if linenumber > linenumber_last:
                # print('WARNING: read excel: table #{t}: banner has no data'.format(t=sheet_name))
                # raise ValueError('WARNING: read excel: table #{t}: banner has no data'.format(t=sheet_name))
                # continue
                pass
            linenumber_data_starts = linenumber
            linenumber = linenumber - 1
            while( (linenumber<=linenumber_last) and (len(rows[linenumber]['col_rest'])==0)):
                linenumber = linenumber - 1
            linenumber_banner_ends = linenumber

            banner_lines_scores = {}
            for i,linenumber in enumerate(range(linenumber_banner_begins,linenumber_banner_ends+1)):
                banner_lines_scores[linenumber] = 0.0
                # 1. count non-empty
                is_empty = True
                row = [trim(s) for s in df_thissheet_clean.iloc[linenumber,1:]]
                for col in row:
                    if len(trim(col))>0:
                        banner_lines_scores[linenumber] = banner_lines_scores[linenumber] + 1.0/len(row)
                        is_empty = False
                # identify stat test row - we exclude almost one point (.99)
                if not is_empty:
                    stat_test = True
                    for col in row:
                        if not re.match(r'^\s*?\w\s*?$',col):
                            stat_test = False
                    if stat_test:
                        banner_lines_scores[linenumber] = banner_lines_scores[linenumber] - .99/len(row)
                # and if we stil have the same scores, we'll take the latest row preferrably - we'll add .01 per row number
                if linenumber_banner_ends-linenumber_banner_begins>1:
                    linenumber_limit_banner_lines_max = int(len([r for r in rows if len(r['col_1'])>0]))
                    if linenumber_limit_banner_lines_max<5:
                        linenumber_limit_banner_lines_max = 5
                    if( linenumber_banner_ends-linenumber_banner_begins<linenumber_limit_banner_lines_max ):
                        banner_lines_scores[linenumber] = banner_lines_scores[linenumber] + .01*i/(linenumber_banner_ends-linenumber_banner_begins)
                    else:
                        banner_lines_scores[linenumber] = banner_lines_scores[linenumber] - .01*i/(linenumber_banner_ends-linenumber_banner_begins)
            
            linenumber_banner_most_informative = max([ (banner_lines_scores[linenumber],linenumber) for linenumber in range(linenumber_banner_begins,linenumber_banner_ends+1) ])[1]
            
            # # check that rows have unique id (first col is an id)
            # # not here
            # for i,linenumber in enumerate(range(linenumber_banner_begins,linenumber_banner_ends+1)):
            #     df_thissheet.iloc[linenumber,0] = 'Banner line #{i}'.format(i=i)

            tab_def['readerinfo_linenumber_banner_begins'] = linenumber_banner_begins
            tab_def['readerinfo_linenumber_banner_ends'] = linenumber_banner_ends
            tab_def['readerinfo_linenumber_data_starts'] = linenumber_data_starts
            tab_def['readerinfo_linenumber_banner_most_informative'] = linenumber_banner_most_informative

            for linenumber in range(0,linenumber_banner_begins):
                if len(trim(rows[linenumber]['col_1']))>0:
                    tab_def['content'].append({'name':'Description Line #{d}'.format(d=linenumber+1),get_column_id(column_zero):trim(rows[linenumber]['col_1'])})
            for linenumber in range(linenumber_banner_begins,linenumber_banner_ends+1):
                if len(trim(rows[linenumber]['col_1']))>0:
                    tab_def['content'].append({'name':'Banner Line #{d}'.format(d=linenumber+1),get_column_id(column_zero):trim(rows[linenumber]['col_1'])+'\t'+trim(rows[linenumber]['col_rest'])})

            # now load this sheet as data

            print('reading excel: reading...')
            df_thissheet = xls.parse(sheet_name=sheet_name, index_col=None, header=linenumber_banner_most_informative)
            df_thissheet_clean = df_thissheet.fillna('')
            # df_thissheet_clean.rename(columns={df_thissheet.columns[0]:'axis(side)'}, inplace=True)

            # check that columns have unique ids
            column_name_override = {}
            col_0_name = column_zero # must be unique
            if col_0_name in df_thissheet_clean.columns:
                raise ValueError('reading excel: Sorry this tool can\'t work if there is a banner point "{f}"; Please name your banner points differently'.format(f=column_zero))
            column_name_override[df_thissheet.columns[0]] = col_0_name
            for i,col in enumerate(df_thissheet_clean.columns):
                if i>0:
                    if not col or re.match(r'^\s*?Unnamed\s*?:\s*?(\d+)\s*?','{f}'.format(f=col),flags=re.I):
                        if i==1:
                            column_name_override[col] = 'Total'
                        else:
                            column_name_override[col] = df_thissheet_clean.columns[i-1]
            column_names_already_used = []
            for i,col in enumerate(df_thissheet_clean.columns):
                col_name =  column_name_override[col] if col in column_name_override else col
                if col_name in column_names_already_used:
                    # duplicate
                    col_name_override_suggest = None
                    col_name_override_counter = 2
                    while True:
                        col_name_override_suggest = '{keep}{added}'.format(keep=col_name,added=' {d}'.format(d=col_name_override_counter))
                        if not(col_name_override_suggest in column_names_already_used):
                            break
                        else:
                            col_name_override_counter = col_name_override_counter + 1
                    col_name = col_name_override_suggest
                column_names_already_used.append(col_name)
                column_name_override[col] = col_name

            df_thissheet_clean.rename(columns=column_name_override, inplace=True)

            # and rows
            LastLine = 'axis(banner)'
            CellItem = 0
            row_names_already_used = []
            for linenumber in range(0,len(df_thissheet_clean.index)):
                row_name = df_thissheet_clean.iloc[linenumber,0]
                row_name_meaningful = trim(row_name)
                if len(row_name_meaningful)>0:
                    CellItem = 0
                    LastLine = row_name_meaningful
                else:
                    row_name_meaningful = LastLine
                row_name_suggested = '{part_main}{part_unique}'.format(part_main=row_name_meaningful,part_unique=' ({qualifier} {d}'.format(qualifier=('CellItem' if not(row_name_meaningful=='axis(banner)') else 'BannerLine #'),d=CellItem))
                if row_name_suggested in row_names_already_used:
                    row_name_override_suggest = None
                    row_name_override_counter = 2
                    while True:
                        row_name_override_suggest = '{keep}{added}'.format(keep=row_name_suggested,added=' [Duplicate #] {d}]'.format(d=row_name_override_counter))
                        if not(row_name_override_suggest in row_names_already_used):
                            break
                        else:
                            row_name_override_counter = row_name_override_counter + 1
                    row_name_suggested = row_name_override_suggest
                row_names_already_used.append(row_name_suggested)
                #df_thissheet_clean.iloc[linenumber,0] = row_name_suggested
                row_def_append = {
                    'name': row_name_suggested,
                    # 'label': df_thissheet_clean.iloc[linenumber,0]
                }
                row = df_thissheet_clean.index[linenumber]
                cols = df_thissheet_clean.columns
                for col in cols:
                    cellvalue = df_thissheet_clean.loc[row,col]
                    prop_add_name = get_column_id(col)
                    prop_add_columntext = col
                    row_def_append[prop_add_name] = cellvalue
                    if not (prop_add_name in tab_def['columns']):
                        tab_def['columns'].append(prop_add_name)
                    if not (prop_add_name in tab_def['column_headers']):
                        tab_def['column_headers'][prop_add_name] = prop_add_columntext
                    if not (prop_add_name in data['report_scheme']['columns']):
                        data['report_scheme']['columns'].append(prop_add_name)
                    if not (prop_add_name in data['report_scheme']['column_headers']):
                        data['report_scheme']['column_headers'][prop_add_name] = prop_add_columntext
                tab_def['content'].append(row_def_append)
                

            # rows = df_thissheet_clean.index
            # cols = df_thissheet_clean.columns

            # # print(tab_def)
            # # for row in rows[0:15]:
            # #     print('[ {s} ]'.format(s=' . '.join( [ '( "{col}": "{data}" )'.format(col=col,data=df_thissheet_clean.loc[row,col]) for col in cols ] )[0:100]))

        except Exception as e:
            print('reading excel: failed when reading sheet "{sn}"'.format(sn=sheet_name))
            raise e
    
    if is_detected_known_format=='lrw':
        data['report_scheme']['flags'].append('excel-type:lrw')
        
    return data





def json_dump_defaulthandler(obj):
    if type(obj).__module__ == np.__name__:
        if isinstance(obj,np.ndarray):
            return obj.tolist()
        else:
            return obj.item()
    raise TypeError('Unknown type: ',type(obj))



def entry_point(config={}):
    time_start = datetime.now()
    parser = argparse.ArgumentParser(
        description="Create a JSON suitable for mdmtoolsap tool, reading a file as text",
        prog='mdmtoolsap --program read_excel'
    )
    parser.add_argument(
        '--inpfile',
        help='Input file',
        type=str,
        required=True
    )
    args = None
    args_rest = None
    if( ('arglist_strict' in config) and (not config['arglist_strict']) ):
        args, args_rest = parser.parse_known_args()
    else:
        args = parser.parse_args()
    inp_file = Path(args.inpfile)

    print('reading Excel: opening {fname}, script started at {dt}'.format(dt=time_start,fname=inp_file))

    data = read_excel(inp_file)

    result_json_fname = ( Path(inp_file).parents[0] / '{basename}{ext}'.format(basename=Path(inp_file).name,ext='.json') if Path(inp_file).is_file() else re.sub(r'^\s*?(.*?)\s*?$',lambda m: '{base}{added}'.format(base=m[1],added='.json'),'{path}'.format(path=inp_file)) )
    print('reading Excel: saving as "{fname}"'.format(fname=result_json_fname))
    outfile = open(result_json_fname, 'w')
    outfile.write(json.dumps(data, indent=4, default=json_dump_defaulthandler))

    time_finish = datetime.now()
    print('reading Excel: finished at {dt} (elapsed {duration})'.format(dt=time_finish,duration=time_finish-time_start))

if __name__ == '__main__':
    entry_point({'arglist_strict':True})
