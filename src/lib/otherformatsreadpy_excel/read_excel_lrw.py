import re
from datetime import datetime, timezone


import pandas as pd




# CONFIG_NAME_DELIMITER = ' ---->>>> '
CONFIG_NAME_DELIMITER = ' / '



def trim(s):
    if s==0:
        return '0'
    if not s:
        return ''
    return '{s}'.format(s=s).strip()





class MDMExcelReadFormatException(Exception):
    """Reading Excel: failed with a given format"""



def lrwexcel_indexsheet_sectionnames_make_unique(section_defs):
    result = [ {**sec_def} for sec_def in section_defs ]
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
    return result

def lrwexcel_read_index_sheet(df_mainpage):

    def validate_check_toc(df_mainpage):
        return ( len( df_mainpage.loc[ df_mainpage[ df_mainpage.columns[0] ].astype('str').str.contains(r'^\s*?Table of Contents\s*?$',regex=True,case=False) ] )>0 )
    
    def detect_toc_row_type(row_txt,prev_results):
        if re.match(r'^\s*?$',row_txt):
            return 'blank'
        elif re.match(r'^\s*?Table of Contents\s*?$',row_txt,flags=re.I):
            return 'toc'
        elif 'toc' in prev_results:
            if re.match(r'^\s*?(?:T|Table)\s*?(\d+)\s*?-\s*(.*?)\s*$',row_txt,flags=re.I):
                return 'table'
            else:
                raise MDMExcelReadFormatException('reading excel: indexsheet: Reading list of tables, passed beyound "Table of Contents", expecting "Table 1 - ...", found something else, unexpected line = {l}, text = {t}'.format(l=row,t=row_txt))
        else:
            return 'preface'
    
    result = []
    result_metadata = []

    if not validate_check_toc(df_mainpage):
        raise MDMExcelReadFormatException
    
    rows = [ df_mainpage.iloc[idx,0] for idx in range(0,len(df_mainpage)) ]

    row_type_prev_results = []
    print('reading excel: reading table names')
    for rownumber,row in enumerate(rows):
        
        row_txt = row
        row_type = detect_toc_row_type(row_txt,row_type_prev_results)
        row_type_prev_results.append(row_type)

        if row_type=='blank':
            continue
        elif row_type=='toc':
            continue
        elif row_type=='table':
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
        elif row_type=='preface':
            if len(trim(row_txt))>0:
                if re.match(r'^\s*?(\w[\w\s]*?)\s*?:.*?$',row_txt,flags=re.I|re.DOTALL):
                    m = re.match(r'^\s*?(\w[\w\s]*?)\s*?:\s*(.*?)\s*$',row_txt,flags=re.I|re.DOTALL)
                    prop_name = m[1]
                    prop_value = m[2]
                    result_metadata.append({'name':prop_name,'value':trim(prop_value)})
                else:
                    result_metadata.append({'name':'line {d}'.format(d=rownumber),'value':trim(row_txt)})
                    # result_metadata.append({'name':'','value':trim(row_txt)})
        else:
            raise AttributeError('reading excel: indexsheet: Reading list of tables, passed beyound "Table of Contents", expecting "Table 1 - ...", found something else, unexpected line = {l}, text = {t}'.format(l=row,t=row_txt))
    
    # check that table names are unique
    result = lrwexcel_indexsheet_sectionnames_make_unique(result)
        
    return result, result_metadata



def lrwexcel_pick_section_entry_or_create_if_missing(sections_to_look_for,sheet_name):
    table_defs = sections_to_look_for
    table_defs_matching = [ tab for tab in [ tab for tab in table_defs if 'number' in tab and tab['number']>0 ] if 'T{n}'.format(n=tab['number'])==sheet_name ]
    if len(table_defs_matching)==0:
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
        df_mainpage = xls.parse( sheet_name='IndexSheet', index_col=None, header=None ).fillna(0)
        print('reading excel: reading index sheet')
        try:
            result,result_metadata = lrwexcel_read_index_sheet(df_mainpage)
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
    
    if not is_detected_known_format:
        raise MDMExcelReadFormatException('not lrw format')

    for sheet_name in [ sheet_name for sheet_name in sheet_names if is_meaningful_sheet(sheet_name) ]:

        try:

            print('reading excel: sheet: {sh}'.format(sh=sheet_name))
            df_thissheet = xls.parse(sheet_name=sheet_name, index_col=None, header=None)

            tab_def = lrwexcel_pick_section_entry_or_create_if_missing(sections_to_look_for=data['sections'],sheet_name=sheet_name)
            
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

            # now load this sheet as data

            print('reading excel: reading...')
            df_thissheet = xls.parse(sheet_name=sheet_name, index_col=None, header=linenumber_banner_most_informative)
            df_thissheet_clean = df_thissheet.fillna('')
            # df_thissheet_clean.rename(columns={df_thissheet.columns[0]:'axis(side)'}, inplace=True)

            # populate column names - check that columns have unique ids
            column_name_override = {}
            column_name_indexbyname = {}
            column_name_namebyindex = {}
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
                col_index = df_thissheet_clean.columns.get_loc(col)
                column_names_already_used.append(col_name)
                column_name_indexbyname[col_name] = col_index
                column_name_namebyindex[col_index] = col_name
                column_name_override[col] = col_name

            df_thissheet_clean.rename(columns=column_name_override, inplace=True)

            # add data for top rows
            df_thissheet = xls.parse(sheet_name=sheet_name, index_col=None, header=None)
            df_thissheet_clean = df_thissheet.fillna('')
            # # df_thissheet_clean.rename(columns={df_thissheet.columns[0]:'axis(side)'}, inplace=True)
            # df_thissheet_clean = df_thissheet.fillna('')
            # rows = [ {'col_1':trim(df_thissheet_clean.iloc[idx,0]),'col_rest':trim(''.join([trim(s) for s in df_thissheet_clean.iloc[idx,1:]]))} for idx in range(0,len(df_thissheet)) ]
            for linenumber in range(0,linenumber_banner_begins):
                # if len(trim(rows[linenumber]['col_1']))>0:
                if True:
                    item_name = 'Description Line #{d}'.format(d=linenumber+1)
                    item_name = '{global_section_name}{separator}{inner_row_name}'.format(
                        global_section_name = '### TABLE DESCRIPTION ###',
                        separator = CONFIG_NAME_DELIMITER,
                        inner_row_name = item_name
                    )
                    row_add = {
                        'name': item_name,
                        # get_column_id(column_zero): trim(rows[linenumber]['col_1'])+'\t'+trim(rows[linenumber]['col_rest'])
                    }
                    for s in [ s for s in range(0,len(df_thissheet_clean.columns)) ]:
                        prop_name = '???'
                        if s==0:
                            prop_name = get_column_id(column_zero)
                        else:
                            prop_name = get_column_id(column_name_namebyindex[s])
                        row_add[prop_name] = trim(df_thissheet_clean.iloc[linenumber,s])
                    tab_def['content'].append(row_add)
            for linenumber in range(linenumber_banner_begins,linenumber_banner_ends+1):
                # if len(trim(rows[linenumber]['col_1']))>0:
                if True:
                    item_name = 'Banner Line #{d}'.format(d=linenumber+1)
                    item_name = '{global_section_name}{separator}{inner_row_name}'.format(
                        global_section_name = '### BANNER ###',
                        separator = CONFIG_NAME_DELIMITER,
                        inner_row_name = item_name
                    )
                    # if linenumber==linenumber_banner_most_informative:
                    #     item_name = ''
                    row_add = {
                        'name': item_name,
                        # get_column_id(column_zero): trim(rows[linenumber]['col_1'])+'\t'+trim(rows[linenumber]['col_rest'])
                    }
                    for s in [ s for s in range(0,len(df_thissheet_clean.columns)) ]:
                        prop_name = '???'
                        if s==0:
                            prop_name = get_column_id(column_zero)
                        else:
                            prop_name = get_column_id(column_name_namebyindex[s])
                        row_add[prop_name] = trim(df_thissheet_clean.iloc[linenumber,s])
                    tab_def['content'].append(row_add)

            # populate row names
            df_thissheet = xls.parse(sheet_name=sheet_name, index_col=None, header=linenumber_banner_most_informative)
            df_thissheet_clean = df_thissheet.fillna('')
            # df_thissheet_clean.rename(columns={df_thissheet.columns[0]:'axis(side)'}, inplace=True)
            df_thissheet_clean.rename(columns=column_name_override, inplace=True)

            LastLine = 'axis(banner)'
            range_lines_to_work_with = range(linenumber_banner_ends+1-linenumber_banner_most_informative,len(df_thissheet_clean.index))

            # detecting section names and grouping rows into sections - quite complicated code! I am feeling like a schoolboy on regional olympiad!
            all_row_labels = []
            row_label_dict = {}
            row_flags_dict = {}
            section_label_dict = {}
            for linenumber in range_lines_to_work_with:
                row_name_clean = re.sub(r'(?:\b(?:(Unweighted)|(?:Effective))\b)?\s*?(\bBase\b)','Base',trim(df_thissheet_clean.iloc[linenumber,0]),flags=re.I)
                if re.match(r'.*?\w.*?',row_name_clean):
                    if( (len(all_row_labels)>0) and (all_row_labels[-1]==row_name_clean) ):
                        # repeating - skip
                        pass
                    else:
                        all_row_labels.append(row_name_clean)
                        row_label_dict[linenumber] = row_name_clean
                        last_section_label = row_name_clean
            if len(all_row_labels)==0:
                all_row_labels.append('???')
            last_section_label = all_row_labels[0]
            for linenumber in range_lines_to_work_with:
                if (linenumber in row_label_dict) and (row_label_dict[linenumber] is not None):
                    # populated - step to next line
                    last_section_label = row_label_dict[linenumber]
                else:
                    row_label_dict[linenumber] = last_section_label
            last_section_label = row_label_dict[range_lines_to_work_with[0]] if len(range_lines_to_work_with)>0 else None
            for linenumber in range_lines_to_work_with:
                rowlabel = row_label_dict[linenumber]
                knt = all_row_labels.count(rowlabel)
                flags = []
                if knt>1:
                    flags.append('repeating')
                elif knt==1:
                    flags.append('unique')
                else:
                    raise AttributeError('please check your code, it shouldn\'t happen')
                section_name = None
                if re.match(r'^\s*?[^\w]*?\bBase\b.*?',rowlabel,flags=re.I):
                    flags.append('base')
                if re.match(r'^\s*?[^\w]*?\bBase\b\s*?[^\w]*?.*?\w.*?',rowlabel,flags=re.I):
                    section_name = re.sub(r'^\s*?[^\w]*?\bBase\b\s*?[^\w]*().*?\w.*?)\s*$',lambda m: m[1],rowlabel,flags=re.I)
                    flags.append('section-name-defined-at-base')
                elif 'unique' in flags:
                    section_name = rowlabel
                else:
                    section_name = None
                if section_name:
                    section_label_dict[linenumber] = section_name
                    last_section_label = section_name
                    flags.append('section-name-definition')
                else:
                    section_label_dict[linenumber] = last_section_label
                offset_above = -1
                while( (linenumber+offset_above>=range_lines_to_work_with[0]) and ( not (len(trim(df_thissheet_clean.iloc[linenumber+offset_above,0]))>0 ) or (trim(df_thissheet_clean.iloc[linenumber+offset_above,0])==trim(df_thissheet_clean.iloc[linenumber,0])) or ( ('base' in flags) and ('base' in row_flags_dict[linenumber+offset_above]) ) ) ):
                    offset_above = offset_above - 1
                if( (linenumber+offset_above<range_lines_to_work_with[0]) or (not(section_label_dict[linenumber]==section_label_dict[linenumber+offset_above])) ):
                    flags.append('section-name-changed')
                row_flags_dict[linenumber] = flags
            # check certain cases
            are_row_sections_defined_above_bases = None
            are_row_sections_defined_below_bases = None
            are_row_sections_defined_at_bases = None
            are_row_sections_defined_no_need_to_define_as_there_s_a_single_section = None
            are_row_sections_defined_with_ultimate_definition_class = None # (any of 3 above)
            # 1. check if row sections are defined above bases
            t = [] # "t" for "temporary" - we count yes or no, checking certain condition, if section name changed above every base (not every, 90% f them), if section name above every base is unique, and it's a row header (all remaining cells are blank)
            for linenumber in range_lines_to_work_with:
                if 'base' in row_flags_dict[linenumber]:
                    offset_above = -1
                    while( (linenumber+offset_above>=range_lines_to_work_with[0]) and ( not (len(trim(df_thissheet_clean.iloc[linenumber+offset_above,0]))>0 ) ) ):
                        offset_above = offset_above - 1
                    if( (linenumber+offset_above>=range_lines_to_work_with[0]) and ('base' in row_flags_dict[linenumber+offset_above]) ):
                        continue
                    val = None
                    offset_above = -1
                    while( (linenumber+offset_above>=range_lines_to_work_with[0]) and ( not (len(trim(df_thissheet_clean.iloc[linenumber+offset_above,0]))>0 ) or (trim(df_thissheet_clean.iloc[linenumber+offset_above,0])==trim(df_thissheet_clean.iloc[linenumber,0])) or ('base' in row_flags_dict[linenumber+offset_above]) ) ):
                        offset_above = offset_above - 1
                    if( (linenumber+offset_above>=range_lines_to_work_with[0]) and ('base' in row_flags_dict[linenumber]) and ( ('unique' in row_flags_dict[linenumber+offset_above]) and ('section-name-changed' in row_flags_dict[linenumber+offset_above]) and (len(trim(''.join([trim(s) for s in df_thissheet_clean.iloc[linenumber+offset_above,1:]])))==0) ) ):
                        val = True
                    else:
                        val = False
                    if val:
                        row_flags_dict[linenumber].append('section-header-above')
                        # linenumber+offset_above is where section starts
                        if linenumber+offset_above>=range_lines_to_work_with[0]:
                            row_flags_dict[linenumber+offset_above].append('section-name-ultimate-definition')
                            row_flags_dict[linenumber+offset_above].append('section-name-ultimate-definition-abovebases')
                    if val is not None:
                        t.append(val)
            are_row_sections_defined_above_bases = ( ( (1.0*len([s for s in t if s])) / (1.0*len(t)) >= .9 ) and (len(t)>2) ) if len(t)>0 else False
            # 2. check if row sections are defined below bases
            t = [] # "t" for "temporary" - we count yes or no, checking certain condition...
            for linenumber in range_lines_to_work_with:
                if 'base' in row_flags_dict[linenumber]:
                    offset_above = -1
                    while( (linenumber+offset_above>=range_lines_to_work_with[0]) and ( not (len(trim(df_thissheet_clean.iloc[linenumber+offset_above,0]))>0) ) ):
                        offset_above = offset_above - 1
                    if( (linenumber+offset_above>=range_lines_to_work_with[0]) and ('base' in row_flags_dict[linenumber+offset_above]) ):
                        continue
                    val = None
                    offset_below = 1
                    while( (linenumber+offset_below<=range_lines_to_work_with[-1]) and ( not (len(trim(df_thissheet_clean.iloc[linenumber+offset_below,0]))>0) or (trim(df_thissheet_clean.iloc[linenumber+offset_below,0])==trim(df_thissheet_clean.iloc[linenumber,0])) or ('base' in row_flags_dict[linenumber+offset_below]) ) ):
                        offset_below = offset_below + 1
                    if( (linenumber+offset_below<=range_lines_to_work_with[-1]) and ('base' in row_flags_dict[linenumber]) and ( ('unique' in row_flags_dict[linenumber+offset_below]) ) ):
                        val = True
                    else:
                        val = False
                    if val:
                        # linenumber is where section starts
                        # linenumber+offset_below is where section label is
                        if linenumber<=range_lines_to_work_with[-1] and linenumber>=range_lines_to_work_with[0] and linenumber+offset_below<=range_lines_to_work_with[-1] and linenumber+offset_below>=range_lines_to_work_with[0]:
                            row_flags_dict[linenumber].append('section-name-ultimate-definition')
                            row_flags_dict[linenumber].append('section-name-ultimate-definition-belowbases')
                            section_label_dict[linenumber] = section_label_dict[linenumber+offset_below]
                    if val is not None:
                        t.append(val)
            are_row_sections_defined_below_bases = ( ( (1.0*len([s for s in t if s])) / (1.0*len(t)) >= .9 ) and (len(t)>2) ) if len(t)>0 else False
            # 3. check if row sections are defined at bases
            t = [] # "t" for "temporary" - we count yes or no, checking certain condition...
            for linenumber in range_lines_to_work_with:
                if 'base' in row_flags_dict[linenumber]:
                    offset_above = -1
                    while( (linenumber+offset_above>=range_lines_to_work_with[0]) and ( not (len(trim(df_thissheet_clean.iloc[linenumber+offset_above,0]))>0 ) ) ):
                        offset_above = offset_above - 1
                    if( (linenumber+offset_above>=range_lines_to_work_with[0]) and ('base' in row_flags_dict[linenumber+offset_above]) ):
                        continue
                    val = None
                    if( ('base' in row_flags_dict[linenumber]) and ('section-name-defined-at-base' in row_flags_dict[linenumber]) and ('section-name-definition' in row_flags_dict[linenumber]) ):
                        val = True
                    else:
                        val = False
                    if val:
                        # linenumber is where section starts
                        row_flags_dict[linenumber].append('section-name-ultimate-definition')
                        row_flags_dict[linenumber].append('section-name-ultimate-definition-atbases')
                    if val is not None:
                        t.append(val)
            are_row_sections_defined_at_bases = ( ( (1.0*len([s for s in t if s])) / (1.0*len(t)) >= .9 ) and (len(t)>2) ) if len(t)>0 else False
            # 4. another attempt, the most simple actually - "normal" table,  single base at the top (or, maybe unweighted, etc...)
            are_row_sections_defined_no_need_to_define_as_there_s_a_single_section = ([l.lower() for l in all_row_labels].count('base')==1) and ([l.lower() for l in all_row_labels].index('base')==0)
            if are_row_sections_defined_no_need_to_define_as_there_s_a_single_section:
                if len(range_lines_to_work_with)>0:
                    row_flags_dict[range_lines_to_work_with[0]].append('section-name-ultimate-definition')
                    row_flags_dict[range_lines_to_work_with[0]].append('section-name-ultimate-definition-simpletable')
                    section_label_dict[range_lines_to_work_with[0]] = tab_def['name']
            # now, take action
            are_row_sections_defined_with_ultimate_definition_class = are_row_sections_defined_above_bases or are_row_sections_defined_below_bases or are_row_sections_defined_at_bases or are_row_sections_defined_no_need_to_define_as_there_s_a_single_section
            if are_row_sections_defined_with_ultimate_definition_class:
                check_flag = 'section-name-ultimate-definition'
                if are_row_sections_defined_no_need_to_define_as_there_s_a_single_section:
                    check_flag = 'section-name-ultimate-definition-simpletable'
                elif are_row_sections_defined_at_bases:
                    check_flag = 'section-name-ultimate-definition-atbases'
                elif are_row_sections_defined_above_bases:
                    check_flag = 'section-name-ultimate-definition-abovebases'
                elif are_row_sections_defined_below_bases:
                    check_flag = 'section-name-ultimate-definition-belowbases'
                last_section_label = section_label_dict[range_lines_to_work_with[0]] if len(range_lines_to_work_with)>0 else None
                for linenumber in range_lines_to_work_with:
                    if check_flag in row_flags_dict[linenumber]:
                        # section_label_dict[linenumber] = section_label_dict[linenumber]
                        last_section_label = section_label_dict[linenumber]
                    else:
                        section_label_dict[linenumber] = last_section_label
            
            # and reset items at the bottom
            if len(range_lines_to_work_with)>0:
                linenumber = range_lines_to_work_with[-1]
                while( (linenumber>=range_lines_to_work_with[0]) and (len(trim(''.join([trim(s) for s in df_thissheet_clean.iloc[linenumber,1:]])))==0) ):
                    # if (len(trim(df_thissheet_clean.iloc[linenumber,0]))>0):
                    if True:
                        section_label_dict[linenumber] = '### FOOTER ###' # tab_def['name']
                    linenumber = linenumber - 1
            # cut one empty row from last last, to normalize the number of line breaks;
            # if we don't do it, normally every line is represented
            # by 3 rows - counts/persents/stat testing,
            # but the last line has 4 rows, just because there's
            # an empty row, and it's added
            linenumber = None
            range_footerlines_all = []
            range_footerlines_empty = []
            for linenumber in range_lines_to_work_with:
                if section_label_dict[linenumber] == '### FOOTER ###':
                    # footer start here
                    range_footerlines_all = range(linenumber,range_lines_to_work_with[-1]+1)
                    break
            for linenumber in range_footerlines_all:
                if len(trim(df_thissheet_clean.iloc[linenumber,0]))>0:
                    # footer non-empty content starts here
                    range_footerlines_empty = range(range_footerlines_all[0],linenumber)
                    break
            if len(range_footerlines_empty)>0:
                linenumber = range_footerlines_empty[-1]
            else:
                linenumber = None
            if linenumber is not None:
                section_label_dict[linenumber] = '### FOOTER ###' # tab_def['name']
                df_thissheet_clean.iloc[linenumber,0] = '-'

            CellItem = 0
            row_names_already_used = []
            for linenumber in range_lines_to_work_with:
                row_name = trim(df_thissheet_clean.iloc[linenumber,0])
                if (linenumber==range_lines_to_work_with[0]) and len(row_name) == 0:
                    row_name = '-' # just something to start with
                if section_label_dict[linenumber] == '### FOOTER ###':
                    if re.match(r'^\s*?Statistics\s*?:\s.*?',row_name,flags=re.I):
                        row_name = 'statistics'
                    elif re.match(r'^\s*?Table \d+.*?',row_name,flags=re.I):
                        row_name = 'table ###'
                    else:
                        row_name = row_name[:10]


                row_name_empty = not(len(row_name)>0)
                if not row_name_empty:
                    row_name = '{global_section_name}{separator}{inner_row_name}'.format(
                        global_section_name = section_label_dict[linenumber],
                        separator = CONFIG_NAME_DELIMITER,
                        inner_row_name = row_name
                    )
                if not row_name_empty:
                    CellItem = 0
                    LastLine = row_name
                else:
                    row_name = LastLine
                row_name_suggested = '{part_main}{part_unique}'.format(
                    part_main = row_name,
                    part_unique = ( (' ({qualifier} {d}'.format(qualifier=('CellItem' if not(row_name=='axis(banner)') else 'BannerLine #'),d=CellItem)) if not('{c}'.format(c=CellItem)=='0') else '' )
                )
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
                row_append = {
                    'name': row_name_suggested,
                    # 'label': df_thissheet_clean.iloc[linenumber,0]
                }
                row = df_thissheet_clean.index[linenumber]
                cols = df_thissheet_clean.columns
                for col in cols:
                    cellvalue = df_thissheet_clean.loc[row,col]
                    prop_add_name = get_column_id(col)
                    prop_add_columntext = col
                    row_append[prop_add_name] = cellvalue
                    if not (prop_add_name in tab_def['columns']):
                        tab_def['columns'].append(prop_add_name)
                    if not (prop_add_name in tab_def['column_headers']):
                        tab_def['column_headers'][prop_add_name] = prop_add_columntext
                    if not (prop_add_name in data['report_scheme']['columns']):
                        data['report_scheme']['columns'].append(prop_add_name)
                    if not (prop_add_name in data['report_scheme']['column_headers']):
                        data['report_scheme']['column_headers'][prop_add_name] = prop_add_columntext
                if not row_name_empty or (len(tab_def['content'])==0):
                    tab_def['content'].append(row_append)
                else:
                    row_update = tab_def['content'][-1]
                    empty_value_filled_linebreaks = ''
                    cells_check_linebreaks = [ str(row_update[colnum]).count('\n') for colnum in [col_id for col_id in tab_def['columns'] if ( (col_id in row_update) and not (col_id=='name') ) ] ]
                    cells_check_linebreaks.sort()
                    empty_value_filled_linebreaks = ''.join(['\n' for p in range(0,cells_check_linebreaks[int(len(cells_check_linebreaks)/2)])])
                    for prop_name in dict.keys({**row_update,**row_append}):
                        if not(prop_name=='name'):
                            row_update[prop_name] = '{part_preserve}\n{part_add}'.format(part_preserve=row_update[prop_name] if prop_name in row_update else empty_value_filled_linebreaks,part_add=row_append[prop_name] if prop_name in row_append else empty_value_filled_linebreaks)
                

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





