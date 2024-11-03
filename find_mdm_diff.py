# import os, time, re, sys
from datetime import datetime, timezone
# from dateutil import tz
import argparse
from pathlib import Path
import re
import json


import helper_diff_wrappers
import helper_utility_wrappers





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
    columns_list_check = [ col for col in helper_diff_wrappers.diff_make_combined_list(d_l['report_scheme']['columns'],d_r['report_scheme']['columns']) if not re.match(r'^\s*?name\s*?$',col,flags=re.I) ]
    for col in columns_list_check:
        columns_list_combined.append('{basename}{suffix}'.format(basename=col,suffix='_left'))
        columns_list_combined.append('{basename}{suffix}'.format(basename=col,suffix='_right'))
    column_headers_combined = {'name':'Item name','flagdiff':'Diff flag'}
    for key in dict.keys({**d_r['report_scheme']['column_headers'],**d_l['report_scheme']['column_headers']}):
        if key in d_l['report_scheme']['column_headers']:
            column_headers_combined['{name}'.format(name=key)] = '{basename}'.format(basename=d_l['report_scheme']['column_headers'][key])
            column_headers_combined['{name}_left'.format(name=key)] = '{basename} (Left MDD)'.format(basename=d_l['report_scheme']['column_headers'][key])
        if key in d_r['report_scheme']['column_headers']:
            if not( '{name}'.format(name=key) in column_headers_combined ):
                column_headers_combined['{name}'.format(name=key)] = '{basename}'.format(basename=d_r['report_scheme']['column_headers'][key])
            column_headers_combined['{name}_right'.format(name=key)] = '{basename} (Right MDD)'.format(basename=d_r['report_scheme']['column_headers'][key])
    flags_list_combined = helper_diff_wrappers.diff_make_combined_list( d_l['report_scheme']['flags'], d_r['report_scheme']['flags'] )
    section_list_combined = helper_diff_wrappers.diff_make_combined_list( [ item['name'] for item in d_l['sections']], [ item['name'] for item in d_r['sections']])
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
            report_rows_diff = helper_diff_wrappers.diff_row_names_respecting_groups( rows_l if '' in rows_l else ['']+rows_l, rows_r if '' in rows_r else ['']+rows_r )
            performance_counter = iter(helper_utility_wrappers.PerformanceMonitor(config={
                'total_records': len(report_rows_diff),
                'report_frequency_records_count': 200,
                'report_frequency_timeinterval': 9
            }))
            for row_diff_item in report_rows_diff:
                try:
                    row_name = row_diff_item.line
                    next(performance_counter)
                    row = {}
                    row['name'] = row_name
                    flag = '???'
                    if row_diff_item.flag == 'keep':
                        flag = '(keep)'
                    elif( (row_name in rows_l) and (row_name in rows_r) ):
                        if row_diff_item.flag == 'remove':
                            flag = '(moved from here)'
                        elif row_diff_item.flag == 'insert':
                            flag = '(moved here)'
                        else:
                            raise AttributeError('Please check diff flag!!!')
                    elif( row_name in rows_l ):
                        flag = '(removed)'
                    elif( row_name in rows_r ):
                        flag = '(added)'
                    row['flagdiff'] = flag
                    mdd_l_rowdata = {}
                    mdd_r_rowdata = {}
                    if( ( (row_name in rows_l) and (row_name in rows_r) ) and (row_diff_item.flag == 'remove') ):
                        # skip for rows moved at their old position
                        pass
                    else:
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
                            result_this_col_left, result_this_col_right = helper_diff_wrappers.diff_values_structural( mdd_l_coldata, mdd_r_coldata )
                        else:
                            mdd_l_coldata = '' if mdd_l_coldata is None else ( json.dumps(mdd_l_coldata) if mdd_l_is_structural else '{fmt}'.format(fmt=mdd_l_coldata) )
                            mdd_r_coldata = '' if mdd_r_coldata is None else ( json.dumps(mdd_r_coldata) if mdd_r_is_structural else '{fmt}'.format(fmt=mdd_r_coldata) )
                            def normalize_linebreaks(t):
                                return re.sub('\r?\n','\n',re.sub('\r','\n',t))
                            mdd_l_coldata = normalize_linebreaks(mdd_l_coldata)
                            mdd_r_coldata = normalize_linebreaks(mdd_r_coldata)
                            result_this_col_left, result_this_col_right = helper_diff_wrappers.diff_values_text( mdd_l_coldata, mdd_r_coldata )
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

