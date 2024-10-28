# import os, time, re, sys
from datetime import datetime, timezone
# from dateutil import tz
import argparse
from pathlib import Path
import re
import json
import time
# from collections import namedtuple
from dataclasses import dataclass


from lib.difflib.diff import Myers


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

# # TODO:
# import pdb


def find_diff(inp_mdd_l,inp_mdd_r):
    d_l = None
    d_r = None
    datetime_start = datetime.now()
    with open(inp_mdd_l) as f_l:
        with open(inp_mdd_r) as f_r:
            d_l = json.load(f_l)
            d_r = json.load(f_r)
    columns_list_combined = [
        'flagdiff', 'name'
    ]
    columns_list_check = []
    for col in Myers.to_records(Myers.diff(d_l['report_scheme']['columns'],d_r['report_scheme']['columns']),d_l['report_scheme']['columns'],d_r['report_scheme']['columns']):
        if not re.match(r'^\s*?name\s*?$',col.line,flags=re.I):
            columns_list_combined.append('{basename}{suffix}'.format(basename=col.line,suffix='_left'))
            columns_list_combined.append('{basename}{suffix}'.format(basename=col.line,suffix='_right'))
            columns_list_check.append('{basename}{suffix}'.format(basename=col.line,suffix=''))
    column_headers_combined = {'name':'Item name','flagdiff':'Diff flag'}
    for key in [ item.line for item in Myers.to_records(Myers.diff(list(dict.keys(d_l['report_scheme']['column_headers'])),list(dict.keys(d_r['report_scheme']['column_headers']))),list(dict.keys(d_l['report_scheme']['column_headers'])),list(dict.keys(d_r['report_scheme']['column_headers']))) ]:
        if key in d_l['report_scheme']['column_headers']:
            column_headers_combined['{name}'.format(name=key)] = '{basename}'.format(basename=d_l['report_scheme']['column_headers'][key])
            column_headers_combined['{name}_left'.format(name=key)] = '{basename} (Left MDD)'.format(basename=d_l['report_scheme']['column_headers'][key])
        if key in d_r['report_scheme']['column_headers']:
            if not( '{name}'.format(name=key) in column_headers_combined ):
                column_headers_combined['{name}'.format(name=key)] = '{basename}'.format(basename=d_r['report_scheme']['column_headers'][key])
            column_headers_combined['{name}_right'.format(name=key)] = '{basename} (Right MDD)'.format(basename=d_r['report_scheme']['column_headers'][key])
    flags_list_combined = [ item.line for item in Myers.to_records(Myers.diff(d_l['report_scheme']['flags'],d_r['report_scheme']['flags']),d_l['report_scheme']['flags'],d_r['report_scheme']['flags']) ]
    section_list_combined = []
    for col in Myers.to_records(Myers.diff([ item['name'] for item in d_l['sections']],[ item['name'] for item in d_r['sections']]),[ item['name'] for item in d_l['sections']],[ item['name'] for item in d_r['sections']]):
        if True:
            section_list_combined.append('{basename}{suffix}'.format(basename=col.line,suffix=''))
    result = {
        'report_type': 'diff',
        'source_left': '{path}'.format(path=inp_mdd_l),
        'source_right': '{path}'.format(path=inp_mdd_l),
        'report_datetime_utc': datetime_start.astimezone(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'report_datetime_local': datetime_start.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'source_file_metadata': [
            { 'name': 'source_left', 'value': '{path}'.format(path=inp_mdd_l) },
            { 'name': 'source_right', 'value': '{path}'.format(path=inp_mdd_r) },
        ],
        'report_scheme': {
            'columns': columns_list_combined,
            'column_headers': column_headers_combined,
            'flags': flags_list_combined
        },
        'sections': [],
    }
    for process_section_name in section_list_combined:
        try:
            print('processing section {name}'.format(name=process_section_name))
            result_this_section = []
            mdd_l_sections_allmatches = [ section for section in d_l['sections'] if section['name']==process_section_name ]
            mdd_r_sections_allmatches = [ section for section in d_r['sections'] if section['name']==process_section_name ]
            mdd_l_sectiondata = ( ( mdd_l_sections_allmatches[0]['content'] if 'content' in mdd_l_sections_allmatches[0] else [] ) if len(mdd_l_sections_allmatches)>0 else [] )
            mdd_r_sectiondata = ( ( mdd_r_sections_allmatches[0]['content'] if 'content' in mdd_r_sections_allmatches[0] else [] ) if len(mdd_r_sections_allmatches)>0 else [] )
            rows_l = [ ( item['name'] if 'name' in item else '???' ) for item in mdd_l_sectiondata ]
            rows_r = [ ( item['name'] if 'name' in item else '???' ) for item in mdd_r_sectiondata ]
            report_rows = [ item.line for item in Myers.to_records(Myers.diff(rows_l,rows_r),rows_l,rows_r) ]
            performance_counter_total_rows = len(report_rows)
            performance_counter_rows_processed = 0
            performance_counter_time_started = time.time()
            performance_counter_time_lastreported = time.time()
            performance_counter_lastreported = -1
            for row_name in report_rows:
                try:
                    performance_counter_rows_processed = performance_counter_rows_processed+ 1
                    if performance_counter_rows_processed - performance_counter_lastreported > 200:
                        performance_time_now = time.time()
                        if (performance_time_now - performance_counter_time_lastreported)>9:
                            print('Checking for diffs in labels, processing line {nline} / {nlinetotal} ({per}%)'.format(nline=performance_counter_rows_processed,nlinetotal=performance_counter_total_rows,per=round(performance_counter_rows_processed*100/performance_counter_total_rows,1)))
                            performance_counter_lastreported = performance_counter_rows_processed
                            performance_counter_time_lastreported = performance_time_now
                    row = {}
                    row['name'] = row_name
                    flag = '???'
                    if( (row_name in rows_l) and (row_name in rows_r) ):
                        flag = '(keep)'
                    elif( row_name in rows_l ):
                        flag = '(removed)'
                    elif( row_name in rows_r ):
                        flag = '(added)'
                    row['flagdiff'] = flag
                    mdd_l_rowdata = {}
                    mdd_r_rowdata = {}
                    if( row_name in rows_l ):
                        mdd_l_rowdata_allrowsmatching = [ row for row in mdd_l_sectiondata if row['name']==row_name ]
                        if len(mdd_l_rowdata_allrowsmatching)>0:
                            mdd_l_rowdata = mdd_l_rowdata_allrowsmatching[0]
                    if( row_name in rows_r ):
                        mdd_r_rowdata_allrowsmatching = [ row for row in mdd_r_sectiondata if row['name']==row_name ]
                        if len(mdd_r_rowdata_allrowsmatching)>0:
                            mdd_r_rowdata = mdd_r_rowdata_allrowsmatching[0]
                    for col in columns_list_check:
                        mdd_l_coldata = mdd_l_rowdata[col] if col in mdd_l_rowdata else None
                        mdd_r_coldata = mdd_r_rowdata[col] if col in mdd_r_rowdata else None
                        mdd_l_is_structural = isinstance(mdd_l_coldata,dict) or isinstance(mdd_l_coldata,list)
                        mdd_r_is_structural = isinstance(mdd_r_coldata,dict) or isinstance(mdd_r_coldata,list)
                        # col_diff = None
                        result_this_col_left = ''
                        result_this_col_right = ''
                        if( mdd_l_is_structural and mdd_r_is_structural ) or ( mdd_l_is_structural and (mdd_r_coldata is None) ) or ( (mdd_l_coldata is None) and mdd_r_is_structural ):
                            if mdd_l_coldata is None:
                                mdd_l_coldata = []
                            if mdd_r_coldata is None:
                                mdd_r_coldata = []
                            mdd_l_prop_names = [ prop['name'] for prop in mdd_l_coldata ]
                            mdd_r_prop_names = [ prop['name'] for prop in mdd_r_coldata ]
                            prop_names_list_combined = [ item.line for item in Myers.to_records(Myers.diff(mdd_l_prop_names,mdd_r_prop_names),mdd_l_prop_names,mdd_r_prop_names) ]
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
                                    prop_val_right = prop_val_right + '<<REMOVED>>' + value_right + '<<ENDREMOVED>>'
                                if propname in mdd_l_prop_names:
                                    result_this_col_left.append({'name':propname,'value':prop_val_left})
                                if propname in mdd_r_prop_names:
                                    result_this_col_right.append({'name':propname,'value':prop_val_right})
                        else:
                            mdd_l_coldata = '' if mdd_l_coldata is None else ( json.dumps(mdd_l_coldata) if mdd_l_is_structural else '{fmt}'.format(fmt=mdd_l_coldata) )
                            mdd_r_coldata = '' if mdd_r_coldata is None else ( json.dumps(mdd_r_coldata) if mdd_r_is_structural else '{fmt}'.format(fmt=mdd_r_coldata) )
                            mdd_l_coldata = re.sub('\r?\n','\n',re.sub('\r','\n',mdd_l_coldata))
                            mdd_r_coldata = re.sub('\r?\n','\n',re.sub('\r','\n',mdd_r_coldata))
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
                                def splitwords(s):
                                    return re.sub(r'((?:\w+)|(?:\r?\n)|(?:\s+))',lambda m:'{delimiter}{preserve}{delimiter}'.format(preserve=m[1],delimiter='<<MDMAPSPLIT>>'),s).split('<<MDMAPSPLIT>>')
                                mdd_l_coldata = splitwords(mdd_l_coldata)
                                mdd_r_coldata = splitwords(mdd_r_coldata)
                                diff_data = Myers.to_records(Myers.diff(mdd_l_coldata,mdd_r_coldata),mdd_l_coldata,mdd_r_coldata)
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
                        row['{col_name}{suffix}'.format(col_name = col,suffix='_left')] = result_this_col_left
                        row['{col_name}{suffix}'.format(col_name = col,suffix='_right')] = result_this_col_right
                    result_this_section.append(row)
                except Exception as e:
                    print('ERROR: something happened when processing row {name}'.format(name=row_name))
                    raise e
            result['sections'].append({'name':process_section_name,'content':result_this_section})
        except Exception as e:
            print('ERROR: something happened when processing section {name}'.format(name=process_section_name))
            raise e
    return result




if __name__ == '__main__':
    time_start = datetime.now()
    parser = argparse.ArgumentParser(
        description="Find Diff"
    )
    parser.add_argument(
        '-1',
        '--mdd_scheme_left',
        help='JSON with fields data from Input MDD A',
        required=True
    )
    parser.add_argument(
        '-2',
        '--mdd_scheme_right',
        help='JSON with fields data from Input MDD B',
        required=True
    )
    args = parser.parse_args()
    inp_mdd_l = ''
    if args.mdd_scheme_left:
        inp_mdd_l = Path(args.mdd_scheme_left)
        inp_mdd_l = '{inp_mdd_l}'.format(inp_mdd_l=inp_mdd_l.resolve())
    else:
        raise FileNotFoundError('Left MDD: file not provided')
    inp_mdd_r = ''
    if args.mdd_scheme_right:
        inp_mdd_r = Path(args.mdd_scheme_right)
        inp_mdd_r = '{inp_mdd_l}'.format(inp_mdd_l=inp_mdd_r.resolve())
    else:
        raise FileNotFoundError('Right MDD: file not provided')
    # inp_file_specs = open(inp_file_specs_name, encoding="utf8")

    if not(Path(inp_mdd_l).is_file()):
        raise FileNotFoundError('file not found: {fname}'.format(fname=inp_mdd_l))
    if not(Path(inp_mdd_r).is_file()):
        raise FileNotFoundError('file not found: {fname}'.format(fname=inp_mdd_r))
    
    print('MDM diff script: script started at {dt}'.format(dt=time_start))

    result = find_diff(inp_mdd_l,inp_mdd_r)
    
    result_json = json.dumps(result, indent=4)
    report_part_mdd_left_filename = re.sub( r'\.mdd\.json', '.mdd', Path(inp_mdd_l).name )
    report_part_mdd_right_filename = re.sub( r'\.mdd\.json', '.mdd', Path(inp_mdd_r).name )
    report_filename = 'report.diff.{mdd_l}-{mdd_r}.json'.format(mdd_l=report_part_mdd_left_filename,mdd_r=report_part_mdd_right_filename)
    result_json_fname = ( Path(inp_mdd_l).parents[0] / report_filename )
    print('MDM diff script: saving as "{fname}"'.format(fname=result_json_fname))
    with open(result_json_fname, "w") as outfile:
        outfile.write(result_json)

    time_finish = datetime.now()
    print('MDM diff script: finished at {dt} (elapsed {duration})'.format(dt=time_finish,duration=time_finish-time_start))

