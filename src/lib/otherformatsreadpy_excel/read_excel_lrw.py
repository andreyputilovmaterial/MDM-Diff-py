import re
from datetime import datetime, timezone


import pandas as pd


# this file is used to read excel

# in lrw way
# so we try to read as lrw
# if can't, we raise an exception, and we are trying to read as "general"

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





# an added exception class that is thrown if the format we are trying to read is not looking like lrw tabs
# we normally use this exception to check format
# - we are just trying to read every excel as lrw, and if we catch this exception, we read excel as of general type
# the other possibility when reading excels (that is not mentioned here) is to read it with ms markitdown
# maybe it can be a better option in some cases
class MDMExcelReadFormatException(Exception):
    """Reading Excel: failed with a given format"""




# a fn to read an Index sheet with TOC
# if something is not matching expected format we just throw MDMExcelReadFormatException
# as a return value, we return both
# "result" will be used to have a pre-populated list of tables
# and "result_metadata" will be used to return client name, project number, etc.. - all that comes at the top
def lrwexcel_read_index_sheet(df_mainpage):

    # a helper fn
    # some preliminary check
    def validate_check_toc(df_mainpage):
        return ( len( df_mainpage.loc[ df_mainpage[ df_mainpage.columns[0] ].astype('str').str.contains(r'^\s*?Table of Contents\s*?$',regex=True,case=False) ] )>0 )
    
    # a helper fn
    # index sheet has the following structure:
    # at the top: client data, client name, project number, etc...
    # then the line "Table of Contents"
    # and then a list of tables
    # so this fn detects which line is it - above TOC, below TOC, or just maybe blank, or it's the line which says "Table of Contents"
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
    
    # a helper fn
    # that ensures that section names are unique
    # it checks the name against a list of names used, and adds something, so that every section name is unique
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
    
    # we return both
    # "result" will be used to have a pre-populated list of tables
    # and "result_metadata" will be used to return client name, project number, etc.. - all that comes at the top
    result = []
    result_metadata = []

    # preliminary check
    if not validate_check_toc(df_mainpage):
        raise MDMExcelReadFormatException
    
    # list of rows to iterate through
    rows = [ df_mainpage.iloc[idx,0] for idx in range(0,len(df_mainpage)) ]

    # a var that captures row types already used (so that we can check if we are abpve or below the "Table of Contents" line)
    row_type_prev_results = []
    print('reading excel: reading table names')
    for rownumber,row in enumerate(rows):
        
        row_txt = row
        row_type = detect_toc_row_type(row_txt,row_type_prev_results)
        row_type_prev_results.append(row_type)

        # index sheet has the following structure:
        # at the top: client data, client name, project number, etc...
        # then the line "Table of Contents"
        # and then a list of tables
        # so we behave differently depending on row type -
        # if it's blank - we skip,
        # if it's preface - we read client name, project number, etc,
        # or if it's a table name - we pre-populate it in a list of tables
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
            # something is off but it should not happen
            raise AttributeError('reading excel: indexsheet: Reading list of tables, passed beyound "Table of Contents", expecting "Table 1 - ...", found something else, unexpected line = {l}, text = {t}'.format(l=row,t=row_txt))
    
    # check that table names are unique
    result = lrwexcel_indexsheet_sectionnames_make_unique(result)
        
    return result, result_metadata



# a helper fn
# we have a list pre-read list of tables created when reading TOC
# now we find a matching entry that has the same table name
# so that we add data to that entry
# or, w create an entry, if we can't find it
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
    is_detected_known_format = None
    global_columnid_lookup = { }
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
        

    if 'IndexSheet' in sheet_names and 'T1' in sheet_names: # lrw format - trying to read TOC (table of contents)
        # lrw format - we are expecting that here, on "IndexSheet", there is a line "Table of Contents", and a list of tables below
        # if there is, we grab table names, and set is_detected_known_format = 'lrw'
        df_mainpage = xls.parse( sheet_name='IndexSheet', index_col=None, header=None ).fillna(0)
        print('reading excel: reading index sheet')
        try:
            result,result_metadata = lrwexcel_read_index_sheet(df_mainpage)
            # "result" is used to have a pre-populated list of tables
            # and "result_metadata" is used to return client name, project number, etc.. - all that comes at the top
            data['sections'].extend( result )
            data['source_file_metadata'].extend( result_metadata )
            is_detected_known_format = 'lrw'
        except MDMExcelReadFormatException:
            pass



    # print('reading excel: reading whole file')
    # df = xls.parse( sheet_name=None, index_col=None, header=0)

    # a helper fn
    # the sheet with TOC is meaningless and the sheet with data is meaningful
    def is_meaningful_sheet(sheet_name):
        if is_detected_known_format=='lrw':
            return  re.match(r'^\s*?(?:T|Table)\s*?\d+\s*?$',sheet_name,flags=re.I)
        return True
    
    # check for "is_detected_known_format" flag - it should be set above
    # if it's not - we are not reading excel of lrw format
    if not is_detected_known_format:
        raise MDMExcelReadFormatException('not lrw format')

    # ok, go
    for sheet_name in [ sheet_name for sheet_name in sheet_names if is_meaningful_sheet(sheet_name) ]:

        try:

            print('reading excel: sheet: {sh}'.format(sh=sheet_name))
            df_thissheet = xls.parse(sheet_name=sheet_name, index_col=None, header=None)

            # we have a list pre-read list of tables created when reading TOC
            # now we find a matching entry that has the same table name
            # so that we add data to that entry
            # or, w create an entry, if we can't find it
            resulting_tab_def = lrwexcel_pick_section_entry_or_create_if_missing(sections_to_look_for=data['sections'],sheet_name=sheet_name)
            
            # inspect sheet contents

            df_thissheet_clean = df_thissheet.fillna('')
            # now a tricky code follows
            # we are trying to detect what we are reading, but it
            # is very different based on project requirements, table and banner structure,
            # and formatting options
            # hm, I should probably add tabs from amazon sellers to tests so that I check it with index scores among cell items
            # I should also add main tabs from disney hulu - last time it failed, it means it's a good test

            # rows is an array of dicts with 2 items: col_1 and col_rest
            # sometimes content is stored as in text file - it is added to first column only
            # and sometimes all sheet is used
            # so we are checking first column and all columns to the right
            # checking if it has data, if it's a banner, if it has something in the first column indicating that this row is representing base or some scale option
            rows = [ {'col_1':trim(df_thissheet_clean.iloc[idx,0]),'col_rest':trim(''.join([trim(s) for s in df_thissheet_clean.iloc[idx,1:]]))} for idx in range(0,len(df_thissheet)) ]

            # we start reading from the top, from row #0
            # and project name and table name should follow
            # if there's no table name - that's a big issue
            # there should be a table name
            # otherway excel files are not properly generated from csv
            # just don't override the default TableDocInitialization.mrs
            # and you'll be fine
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
                
            # ok, we found the first row where we have data to then right
            # it means, we stopped reading client name,
            #     ...project name, table name, filter definitions, weight scheme, maybe stat testing, table level info, or other information that is printed at the top
            linenumber_banner_begins = linenumber
            # linenumber = linenumber + 1 # ??? why is that? this rows seems unnecessary; suppressed for now
            while( (linenumber<=linenumber_last) and (len(rows[linenumber]['col_1'])==0) and (len(rows[linenumber]['col_rest'])>0) ):
                linenumber = linenumber + 1
            if linenumber > linenumber_last:
                # print('WARNING: read excel: table #{t}: banner has no data'.format(t=sheet_name))
                # raise ValueError('WARNING: read excel: table #{t}: banner has no data'.format(t=sheet_name))
                # continue
                pass

            # ok, we found the row where we have something in the first column - it means data starts here, we are no longer reading banner

            # we come back a little bit removing blank rows so that blank rows are not counted as banner rows
            linenumber_data_starts = linenumber
            linenumber = linenumber - 1
            while( (linenumber<=linenumber_last) and (len(rows[linenumber]['col_rest'])==0)):
                linenumber = linenumber - 1
            linenumber_banner_ends = linenumber

            # and now a tricky code follows
            # the goal is to find the right row with banner points
            # we should pick the right row with column names
            # this is called "linenumber_banner_most_informative"

            # the rules are the following
            # - it should be populated
            # - ideally banner point names are unique - but unfortunately we know we can't guarantee it - we hope qa reports if we are using the same name, but there's no guarantee
            # - we should detect the row with stat testing letters and skip it
            # as everything here is not a 100% rule, are assigning scores for every rule, and then we pick the row with the highest points
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
            
            # now we pick the row with the highest score - it is the row with banner points, we are using it as column names
            # this is called "linenumber_banner_most_informative"
            linenumber_banner_most_informative = max([ (banner_lines_scores[linenumber],linenumber) for linenumber in range(linenumber_banner_begins,linenumber_banner_ends+1) ])[1]
            # done
            
            # we'll store our findings
            # we don't need it but it's nice to have everything recorded
            resulting_tab_def['readerinfo_linenumber_banner_begins'] = linenumber_banner_begins
            resulting_tab_def['readerinfo_linenumber_banner_ends'] = linenumber_banner_ends
            resulting_tab_def['readerinfo_linenumber_data_starts'] = linenumber_data_starts
            resulting_tab_def['readerinfo_linenumber_banner_most_informative'] = linenumber_banner_most_informative

            print('reading excel: reading...')

            # populate column names - check that columns have unique ids
            # we already read banner info
            # and a line that contains column names
            # but we still don't have that stored in a variable
            # we did not ensure that column names are unique
            # so we are doing it now

            # there are rows that should be skipped - below that meaningful banner line before data starts
            # but we don't care about it now because we only need to read column names, we are now reading anything beyond it

            df_thissheet = xls.parse(sheet_name=sheet_name, index_col=None, header=linenumber_banner_most_informative)
            df_thissheet_clean = df_thissheet.fillna('')
            # df_thissheet_clean.rename(columns={df_thissheet.columns[0]:'axis(side)'}, inplace=True)

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
            # ok, we finished finding final column names

            # now read all data

            # 1. first we start with client name, table name, weight variable, level of population...
            # 2. then we read banner
            # 3 then we read remaining part - all data
            # and final information about stat testing and table number at the bottom

            # add data for top rows, everything above the banner - clieent, project name, table name, weighting variable, status, level of population, etc...
            df_thissheet = xls.parse(sheet_name=sheet_name, index_col=None, header=None)
            df_thissheet_clean = df_thissheet.fillna('')
            for linenumber in range(0,linenumber_banner_begins):
                # if len(trim(rows[linenumber]['col_1']))>0:
                if True:
                    item_name = 'Description Line #{d}'.format(d=linenumber+1)
                    item_name = '{global_section_name}{separator}{inner_row_name}'.format(
                        global_section_name = '### TABLE DESCRIPTION ###',
                        separator = CONFIG_NAME_DELIMITER,
                        inner_row_name = item_name
                    )
                    resulting_row_add = {
                        'name': item_name,
                        # get_column_id(column_zero): trim(rows[linenumber]['col_1'])+'\t'+trim(rows[linenumber]['col_rest'])
                    }
                    for column_number in [ column_number for column_number in range(0,len(df_thissheet_clean.columns)) ]:
                        prop_name = '???'
                        if column_number==0:
                            prop_name = get_column_id(column_zero)
                        else:
                            prop_name = get_column_id(column_name_namebyindex[column_number])
                        resulting_row_add[prop_name] = trim(df_thissheet_clean.iloc[linenumber,column_number])
                    resulting_tab_def['content'].append(resulting_row_add)
            
            # add data for banner
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
                    resulting_row_add = {
                        'name': item_name,
                        # get_column_id(column_zero): trim(rows[linenumber]['col_1'])+'\t'+trim(rows[linenumber]['col_rest'])
                    }
                    for column_number in [ column_number for column_number in range(0,len(df_thissheet_clean.columns)) ]:
                        prop_name = '???'
                        if column_number==0:
                            prop_name = get_column_id(column_zero)
                        else:
                            prop_name = get_column_id(column_name_namebyindex[column_number])
                        resulting_row_add[prop_name] = trim(df_thissheet_clean.iloc[linenumber,column_number])
                    resulting_tab_def['content'].append(resulting_row_add)

            # now load this sheet as data
            # NOTICE: we are loading data from "linenumber_banner_most_informative" line
            # so that Pandas is using it as a header
            # but then there is some number of rows between that line (that is in the middle of the banner), and then there are several blank lines above the data
            # so there are several lines that we should skip

            # populate row names
            df_thissheet = xls.parse(sheet_name=sheet_name, index_col=None, header=linenumber_banner_most_informative)
            df_thissheet_clean = df_thissheet.fillna('')
            df_thissheet_clean.rename(columns=column_name_override, inplace=True)

            LastLine = 'axis(banner)'
            range_lines_to_work_with = range(linenumber_banner_ends+1-linenumber_banner_most_informative,len(df_thissheet_clean.index))

            # detecting section names and grouping rows into sections - quite complicated code! I am feeling like a schoolboy on regional olympiad!
            # that's the most compicated part
            # I am tryong to recognize different schemes - base, and then name, or name, and then base, or base: name, etc...
            # obviously, everything is much more simple if we have normal tables with one single base
            all_row_labels = []
            row_label_dict = {}
            row_flags_dict = {}
            # "row_flags_dict" variable stores a combination of flags
            # while we iterate over rows and data, we are doing certain checks and we are trying to detect what does this row stand for
            # some rows are "Base", some rows contain scale points, some could possibly contain a valuable information of what are we tabulating here, i.e. the word "Disney" or "Hulu" or "Netfix"
            # and it is important to recognize so that we know what data is tabulated here
            # are those counts and percents for Disney or Hulu or Netflix
            # so that we can properly compare data given that knolledge what is tabulated
            # but we can't always reliably tell what is tabulated, because the format can be very different - brand names could come above bases, below base, or after the semicolon in the base row...
            # so, while reading, we assign flags
            # like oh, that row is looking like base, we'll add a flag that it's an analysisbase element - we'll add a flag for it
            # oh that row contains some text that is unique - it can possibly contain brand name - we'll add a flag for it
            # so we are doing our checks and we add flags stored in row_flags_dict
            # and then, analyzing these flags, we understand where do we read group name from
            # "group name" - I mean a if there is a scale for Disney, Disney is the group name, or we have the same scale repeated for Hulu - so we assign disney or hulu as a group name, that should be unique
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
                    section_name = re.sub(r'^\s*?[^\w]*?\bBase\b\s*?[^\w]*?(.*?\w.*?)\s*$',lambda m: m[1],rowlabel,flags=re.I)
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
            # I said we are going to recognize certain patterns - base and then name, or name and then base, or base: name, etc...
            # Here are variables that act as flags for those patterns
            are_row_sections_defined_above_bases = None
            are_row_sections_defined_below_bases = None
            are_row_sections_defined_at_bases = None
            are_row_sections_defined_with_ultimate_definition_class = None # (any of 3 above)
            are_row_sections_defined_no_need_to_define_as_there_s_a_single_section = None
            # 1. check if row sections are defined above bases
            # we find base, and rows above it (non-blank) should be unique, and there should be enough such rows
            findings_count = [] # we count yes or no, checking certain condition, if section name changed above every base (not every, 90% f them), if section name above every base is unique, and it's a row header (all remaining cells are blank)
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
                        findings_count.append(val)
            are_row_sections_defined_above_bases = ( ( (1.0*len([s for s in findings_count if s])) / (1.0*len(findings_count)) >= .9 ) and (len(findings_count)>2) ) if len(findings_count)>0 else False
            # 2. check if row sections are defined below bases
            findings_count = [] # we count yes or no, checking certain condition...
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
                        findings_count.append(val)
            are_row_sections_defined_below_bases = ( ( (1.0*len([s for s in findings_count if s])) / (1.0*len(findings_count)) >= .9 ) and (len(findings_count)>2) ) if len(findings_count)>0 else False
            # 3. check if row sections are defined at bases
            findings_count = [] # we count yes or no, checking certain condition...
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
                        findings_count.append(val)
            are_row_sections_defined_at_bases = ( ( (1.0*len([s for s in findings_count if s])) / (1.0*len(findings_count)) >= .9 ) and (len(findings_count)>2) ) if len(findings_count)>0 else False
            # 4. another attempt, the most simple actually - "normal" table,  single base at the top (or, maybe unweighted, etc...)
            are_row_sections_defined_no_need_to_define_as_there_s_a_single_section = ([l.lower() for l in all_row_labels].count('base')==1) and ([l.lower() for l in all_row_labels].index('base')==0)
            if are_row_sections_defined_no_need_to_define_as_there_s_a_single_section:
                if len(range_lines_to_work_with)>0:
                    row_flags_dict[range_lines_to_work_with[0]].append('section-name-ultimate-definition')
                    row_flags_dict[range_lines_to_work_with[0]].append('section-name-ultimate-definition-simpletable')
                    section_label_dict[range_lines_to_work_with[0]] = resulting_tab_def['name']
            # now, take action
            are_row_sections_defined_with_ultimate_definition_class = are_row_sections_defined_above_bases or are_row_sections_defined_below_bases or are_row_sections_defined_at_bases or are_row_sections_defined_no_need_to_define_as_there_s_a_single_section
            if are_row_sections_defined_with_ultimate_definition_class:
                check_flag = 'section-name-ultimate-definition'
                # these flags are stored in row_flags_dict
                # if there's a "section-name-ultimate-definition" flag, it means that the name of the section should be grabbed from this row. This is the row that indicates name for the section
                # for example, if there is a scale for disney, and then a scale for hulu, and then a scale for netflix - the item that contains "section-name-ultimate-definition" flag is the line where we read "disney" or "hulu" or "netflix"
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
            # explanation
            # when we are reading row by row, etc... we have certain group names assigned. For example, we have a scale with Disney stubs, then we have a scale with Hulu stubs... etc
            # so we assign "Disney" or "Hulu" as a group name
            # but then we have some standard text at the bottom
            # usually stat testing and table number
            # but we should stop assigning our group names
            # statistics or table number is a general information, it should not be named with the last group name, for example, disney or hulu or netflix
            if len(range_lines_to_work_with)>0:
                linenumber = range_lines_to_work_with[-1]
                while( (linenumber>=range_lines_to_work_with[0]) and (len(trim(''.join([trim(s) for s in df_thissheet_clean.iloc[linenumber,1:]])))==0) ):
                    # if (len(trim(df_thissheet_clean.iloc[linenumber,0]))>0):
                    if True:
                        section_label_dict[linenumber] = '### FOOTER ###' # resulting_tab_def['name']
                    linenumber = linenumber - 1
            # one more modification
            # cut one empty row from last row, to normalize the number of line breaks;
            # if we don't do it, normally every line is represented
            # by 3 rows - counts/persents/stat testing,
            # but the last line has 4 rows, just because there's
            # an empty row, and it's added
            # we can't leave it, because our rows will be different - most of them represented in 3 lines and the last represented in 4 lines,
            # so they can't be compared with diff, they are diffrent
            # so we need to cut that 4th line and leave only 3, same as every other row
            # in short, cut one line from last item if there's an empty line that can be cut
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
                section_label_dict[linenumber] = '### FOOTER ###' # resulting_tab_def['name']
                df_thissheet_clean.iloc[linenumber,0] = '-'
            
            # go! main part! read data!
            CellItem = 0
            row_names_already_used = []
            for linenumber in range_lines_to_work_with:

                # row name
                # first we need to find it
                row_name = trim(df_thissheet_clean.iloc[linenumber,0])
                if (linenumber==range_lines_to_work_with[0]) and len(row_name) == 0:
                    row_name = '-' # just something to start with
                if section_label_dict[linenumber] == '### FOOTER ###':
                    if re.match(r'^\s*?Statistics\s*?:\s.*?',row_name,flags=re.I):
                        row_name = 'statistics'
                    elif re.match(r'^\s*?Table \d+.*?',row_name,flags=re.I):
                        row_name = 'table ###'
                    else:
                        row_name = row_name[:10] # it seems 10 is enough so that essential part is included and non-essential is cut

                # the logic here is the following
                # if there is a row name - we are writing data to a new row
                # and if there is no row name - we add contents to the previous row
                # so that cell counts, percents, and stat testing are stored within one single cell
                is_row_name_empty = not(len(row_name)>0)
                if not is_row_name_empty:
                    row_name = '{global_section_name}{separator}{inner_row_name}'.format(
                        global_section_name = section_label_dict[linenumber],
                        separator = CONFIG_NAME_DELIMITER,
                        inner_row_name = row_name
                    )
                if not is_row_name_empty:
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

                # ok, we have row name now
                resulting_row_append = {
                    'name': row_name_suggested,
                    # 'label': df_thissheet_clean.iloc[linenumber,0]
                }
                row = df_thissheet_clean.index[linenumber]
                cols = df_thissheet_clean.columns
                for col in cols:
                    cellvalue = df_thissheet_clean.loc[row,col] # TODO: handle zeros
                    prop_add_name = get_column_id(col)
                    prop_add_columntext = col
                    resulting_row_append[prop_add_name] = cellvalue
                    if not (prop_add_name in resulting_tab_def['columns']):
                        resulting_tab_def['columns'].append(prop_add_name)
                    if not (prop_add_name in resulting_tab_def['column_headers']):
                        resulting_tab_def['column_headers'][prop_add_name] = prop_add_columntext
                    if not (prop_add_name in data['report_scheme']['columns']):
                        data['report_scheme']['columns'].append(prop_add_name)
                    if not (prop_add_name in data['report_scheme']['column_headers']):
                        data['report_scheme']['column_headers'][prop_add_name] = prop_add_columntext
                # I said the logic is
                # if we have a row name, are add a row to our data
                # and if there is no row name, we append to the last row
                if not is_row_name_empty or (len(resulting_tab_def['content'])==0):
                    # we have a row name
                    # we should append a new row to the data
                    resulting_tab_def['content'].append(resulting_row_append)
                else:
                    # we have no row name
                    # we need to uppend contents to the last row
                    # and we need to maintain consistent number of line breaks here
                    # like, if we are adding a 3rd cell item, there should be 2 line breaks above it, so that everything is aligned as it should

                    # the last row
                    # that we are going to update
                    row_update = resulting_tab_def['content'][-1]

                    # a placeholder
                    empty_value_filled_linebreaks = ''

                    # a list of all cells with line breaks counts
                    cells_check_linebreaks = [ str(row_update[colnum]).count('\n') for colnum in [col_id for col_id in resulting_tab_def['columns'] if ( (col_id in row_update) and not (col_id=='name') ) ] ]
                    # we sort
                    cells_check_linebreaks.sort()
                    # and we find median
                    # TODO: oh, that is not 100% efficient (I know the difference is zero, but still not beautiful); the complexity of sort is n.log(n) and complexity of finding median should be linear; so I should not be finding median through sorting
                    # so we have the most common number of line breaks
                    # and we generate a string with that number of line breaks
                    # so that if there is no prior value, we add an empty string with required number of line breaks
                    empty_value_filled_linebreaks = ''.join(['\n' for p in range(0,cells_check_linebreaks[int(len(cells_check_linebreaks)/2)])])

                    # and add contents to every cell
                    for prop_name in dict.keys({**row_update,**resulting_row_append}):
                        if not(prop_name=='name'):
                            row_update[prop_name] = '{part_preserve}\n{part_add}'.format(part_preserve=row_update[prop_name] if prop_name in row_update else empty_value_filled_linebreaks,part_add=resulting_row_append[prop_name] if prop_name in resulting_row_append else empty_value_filled_linebreaks)
                
                # done, all is added or updated!
                

        except Exception as e:
            print('reading excel: failed when reading sheet "{sn}"'.format(sn=sheet_name))
            raise e
    
    if is_detected_known_format=='lrw':
        data['report_scheme']['flags'].append('excel-type:lrw')
        
    return data





