# import os, time, re, sys
import os
from datetime import datetime, timezone
# from dateutil import tz
import argparse
from pathlib import Path
import re
import json



if __name__ == '__main__':
    # run as a program
    import helper_diff_wrappers
    import helper_utility_wrappers
elif '.' in __name__:
    # package
    from . import helper_diff_wrappers
    from . import helper_utility_wrappers
else:
    # included with no parent package
    import helper_diff_wrappers
    import helper_utility_wrappers





def find_diff(data_left,data_right,config):

    datetime_start = datetime.now()
    config_default = {
        'format': '2col'
    }
    config = {**config_default,**config}
    config_diff_format = config['format']

    if not(config_diff_format=='2col'):
        raise Exception('diff format=="{fmt}": not supported, or not implemented'.format(fmt=config_diff_format))

    columns_list_combined = [
        'flagdiff', 'name'
    ]
    columns_list_check = [ col for col in helper_diff_wrappers.diff_make_combined_list(data_left['report_scheme']['columns'],data_right['report_scheme']['columns']) if not re.match(r'^\s*?name\s*?$',col,flags=re.I) ]
    for col in columns_list_check:
        columns_list_combined.append('{basename}{suffix}'.format(basename=col,suffix='_left'))
        columns_list_combined.append('{basename}{suffix}'.format(basename=col,suffix='_right'))
    column_headers_combined = {'name':'Item name','flagdiff':'Diff flag'}
    for key in dict.keys({**data_right['report_scheme']['column_headers'],**data_left['report_scheme']['column_headers']}):
        if key in data_left['report_scheme']['column_headers']:
            column_headers_combined['{name}'.format(name=key)] = '{basename}'.format(basename=data_left['report_scheme']['column_headers'][key])
            column_headers_combined['{name}_left'.format(name=key)] = '{basename} (Left file)'.format(basename=data_left['report_scheme']['column_headers'][key])
        if key in data_right['report_scheme']['column_headers']:
            if not( '{name}'.format(name=key) in column_headers_combined ):
                column_headers_combined['{name}'.format(name=key)] = '{basename}'.format(basename=data_right['report_scheme']['column_headers'][key])
            column_headers_combined['{name}_right'.format(name=key)] = '{basename} (Right file)'.format(basename=data_right['report_scheme']['column_headers'][key])
    flags_list_combined = helper_diff_wrappers.diff_make_combined_list( data_left['report_scheme']['flags'] if 'flags' in data_left['report_scheme'] else [], data_right['report_scheme']['flags'] if 'flags' in data_right['report_scheme'] else [] )
    section_list_combined = helper_diff_wrappers.diff_make_combined_list( [ item['name'] for item in data_left['sections']], [ item['name'] for item in data_right['sections']])

    result = {
        'report_type': 'diff',
        'source_left': '{path}'.format(path=config['inp_filename_left']),
        'source_right': '{path}'.format(path=config['inp_filename_left']),
        'report_datetime_utc': datetime_start.astimezone(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'report_datetime_local': datetime_start.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'source_file_metadata': [
            { 'name': 'source_left', 'value': '{path}'.format(path=config['inp_filename_left']) },
            { 'name': 'source_right', 'value': '{path}'.format(path=config['inp_filename_right']) },
        ],
        'report_scheme': {
            'columns': columns_list_combined,
            'column_headers': column_headers_combined,
            'flags': flags_list_combined
        },
        'sections': [],
    }
    for section_name in section_list_combined:
        try:
            print('processing section {name}'.format(name=section_name))
            result_this_section = []
            file_l_sections_allmatches = [ section for section in data_left['sections'] if section['name']==section_name ]
            file_r_sections_allmatches = [ section for section in data_right['sections'] if section['name']==section_name ]
            file_l_sectiondata = ( ( file_l_sections_allmatches[0]['content'] if 'content' in file_l_sections_allmatches[0] else [] ) if len(file_l_sections_allmatches)>0 else [] )
            file_r_sectiondata = ( ( file_r_sections_allmatches[0]['content'] if 'content' in file_r_sections_allmatches[0] else [] ) if len(file_r_sections_allmatches)>0 else [] )
            rows_l = [ ( item['name'] if 'name' in item else '???' ) for item in file_l_sectiondata ]
            rows_r = [ ( item['name'] if 'name' in item else '???' ) for item in file_r_sectiondata ]
            report_rows_diff = helper_diff_wrappers.finddiff_row_names_respecting_groups( rows_l if '' in rows_l else ['']+rows_l, rows_r if '' in rows_r else ['']+rows_r )
            performance_counter = iter(helper_utility_wrappers.PerformanceMonitor(config={
                'total_records': len(report_rows_diff),
                'report_frequency_records_count': 150,
                'report_frequency_timeinterval': 6
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
                    file_l_rowdata = {}
                    file_r_rowdata = {}
                    if( ( (row_name in rows_l) and (row_name in rows_r) ) and (row_diff_item.flag == 'remove') ):
                        # skip for rows moved at their old position
                        pass
                    else:
                        if( row_name in rows_l ):
                            file_l_rowdata_allrowsmatching = [ row for row in file_l_sectiondata if row['name']==row_name ]
                            if len(file_l_rowdata_allrowsmatching)>0:
                                file_l_rowdata = file_l_rowdata_allrowsmatching[0]
                        if( row_name in rows_r ):
                            file_r_rowdata_allrowsmatching = [ row for row in file_r_sectiondata if row['name']==row_name ]
                            if len(file_r_rowdata_allrowsmatching)>0:
                                file_r_rowdata = file_r_rowdata_allrowsmatching[0]
                    for col in columns_list_check:
                        file_l_coldata = file_l_rowdata[col] if col in file_l_rowdata else None
                        file_r_coldata = file_r_rowdata[col] if col in file_r_rowdata else None
                        file_l_is_structural = isinstance(file_l_coldata,dict) or isinstance(file_l_coldata,list)
                        file_r_is_structural = isinstance(file_r_coldata,dict) or isinstance(file_r_coldata,list)
                        # col_diff = None
                        result_this_col_left = ''
                        result_this_col_right = ''
                        if( file_l_is_structural and file_r_is_structural ) or ( file_l_is_structural and (file_r_coldata is None) ) or ( (file_l_coldata is None) and file_r_is_structural ):
                            if file_l_coldata is None:
                                file_l_coldata = []
                            if file_r_coldata is None:
                                file_r_coldata = []
                            result_this_col_left, result_this_col_right = helper_diff_wrappers.finddiff_values_structural( file_l_coldata, file_r_coldata )
                        else:
                            file_l_coldata = '' if file_l_coldata is None else ( json.dumps(file_l_coldata) if file_l_is_structural else '{fmt}'.format(fmt=file_l_coldata) )
                            file_r_coldata = '' if file_r_coldata is None else ( json.dumps(file_r_coldata) if file_r_is_structural else '{fmt}'.format(fmt=file_r_coldata) )
                            def normalize_linebreaks(t):
                                return re.sub('\r?\n','\n',re.sub('\r','\n',t))
                            file_l_coldata = normalize_linebreaks(file_l_coldata)
                            file_r_coldata = normalize_linebreaks(file_r_coldata)
                            result_this_col_left, result_this_col_right = helper_diff_wrappers.finddiff_values_text( file_l_coldata, file_r_coldata )
                        row['{col_name}{suffix}'.format(col_name = col,suffix='_left')] = result_this_col_left
                        row['{col_name}{suffix}'.format(col_name = col,suffix='_right')] = result_this_col_right
                    result_this_section.append(row)
                except Exception as e:
                    print('ERROR: something happened when processing row {name}'.format(name=row_name))
                    raise e
            section_title = section_name
            if section_name in [ item['name'] for item in data_left['sections']]:
                section_left = [ item for item in data_left['sections']][0]
                if 'title' in section_left:
                    section_title = section_left['title']
            if section_name in [ item['name'] for item in data_right['sections']]:
                section_left = [ item for item in data_right['sections']][0]
                if 'title' in section_left:
                    section_title = section_left['title']
            section_add = {
                'name': section_name,
                'title': section_title,
                'content': result_this_section
            }
            result['sections'].append(section_add)
        except Exception as e:
            print('ERROR: something happened when processing section {name}'.format(name=section_name))
            raise e
    return result









def entry_point(runscript_config={}):

    time_start = datetime.now()
    script_name = 'mdmtoolsap diff script'

    parser = argparse.ArgumentParser(
        description="Find Diff",
        prog='diffscript'
    )
    parser.add_argument(
        '-1',
        '--cmp-scheme-left',
        type=str,
        help='JSON with fields data from Input File A',
        required=True
    )
    parser.add_argument(
        '-2',
        '--cmp-scheme-right',
        type=str,
        help='JSON with fields data from Input File B',
        required=True
    )
    parser.add_argument(
        '--cmp-format',
        help='Format: print results as 2 separate columns, or combine; possible values: 2col (default), 2col_distant, combined',
        type=str,
        required=False
    )
    parser.add_argument(
        '--output-filename',
        help='Set preferred output file name, with path',
        type=str,
        required=False
    )
    parser.add_argument(
        '--output-filename-prefix',
        help='Set additional prefix added to output file name (not working if --output-filename is set)',
        type=str,
        required=False
    )
    parser.add_argument(
        '--output-filename-suffix',
        help='Set additional suffix added to output file name (not working if --output-filename is set)',
        type=str,
        required=False
    )
    parser.add_argument(
        '--norun-special-onlyprintoutputfilename',
        help='A special flag, the script does not run, does not read input files, does not cal;culate diff, does not write anything to files, does not print messages - it only print resulting output file name to console',
        action='store_true',
        required=False
    )
    args = None
    args_rest = None
    if( ('arglist_strict' in runscript_config) and (not runscript_config['arglist_strict']) ):
        args, args_rest = parser.parse_known_args()
    else:
        args = parser.parse_args()
    
    inp_filename_left = ''
    if args.cmp_scheme_left:
        inp_filename_left = Path(args.cmp_scheme_left)
        inp_filename_left = '{inp_filename_left}'.format(inp_filename_left=inp_filename_left.resolve())
    else:
        raise FileNotFoundError('Left CMP Source: file not provided; please use --cmp-scheme-left option')
    inp_filename_right = ''
    if args.cmp_scheme_right:
        inp_filename_right = Path(args.cmp_scheme_right)
        inp_filename_right = '{inp_filename_left}'.format(inp_filename_left=inp_filename_right.resolve())
    else:
        raise FileNotFoundError('Right CMP Source: file not provided; please use --cmp-scheme-right option')
    # inp_file_specs = open(inp_file_specs_name, encoding="utf8")

    diff_format = '2col'
    if args.cmp_format:
        diff_format = args.cmp_format
        fmts_allowed = ['2col','2col_distant','combined']
        if not (diff_format in fmts_allowed):
            raise ValueError('diff: unsupported config option: diff format: "{fmt}"; you can only use [ {allowed} ]'.format(fmt=diff_format,alowed=', '.join(fmts_allowed)))

    diff_config = {
        'format': diff_format,
        'inp_filename_left': inp_filename_left,
        'inp_filename_right': inp_filename_right
    }

    report_part_filename_left = re.sub( r'\.json\s*?$', '', Path(inp_filename_left).name )
    report_part_filename_right = re.sub( r'\.json\s*?$', '', Path(inp_filename_right).name )
    result_final_fname = ''
    if args.output_filename:
        result_final_fname = Path(args.output_filename)
        if args.output_filename_prefix:
            raise FileNotFoundError('diff script: --output-filename-prefix: this option can\'t be set when --output-filename is provided')
        if args.output_filename_suffix:
            raise FileNotFoundError('diff script: --output-filename-suffix: this option can\'t be set when --output-filename is provided')
    else:
        def validate_fname_part(path):
            try:
                return '{path}'.format(path=path) == '{path}'.format(path=Path(path).name)
            except Exception:
                return False
        report_filename_prefixpart = 'report.diff.'
        report_filename_suffixpart = ''
        if args.output_filename_prefix:
            report_filename_prefixpart = args.output_filename_prefix
            if not validate_fname_part(report_filename_prefixpart):
                raise FileNotFoundError('diff script: output filename prefix: not valid name (please check the --output-filename-prefix option you are passing)')
        if args.output_filename_suffix:
            report_filename_suffixpart = args.output_filename_suffix
            if not validate_fname_part(report_filename_suffixpart):
                raise FileNotFoundError('diff script: output filename suffix: not valid name (please check the --output-filename-suffix option you are passing)')
        report_filename_filepart = '{fname_prefix}{file_l}-{file_r}{fname_suffix}.json'.format(file_l=report_part_filename_left,file_r=report_part_filename_right,fname_prefix=report_filename_prefixpart,fname_suffix=report_filename_suffixpart)
        # report_filename_pathpart = Path(inp_filename_left).parents[0]
        report_filename_pathpart = Path(inp_filename_right).parents[0] # right!
        # the right compared source is now the destination for the report -
        # we usually compare something from the past to our working copy,
        # and we need results where are working copy is
        result_final_fname = report_filename_pathpart / report_filename_filepart
    
    if args.norun_special_onlyprintoutputfilename:
        print(result_final_fname)
        exit(0)

    if not(Path(inp_filename_left).is_file()):
        raise FileNotFoundError('file not found: {fname}'.format(fname=inp_filename_left))
    if not(Path(inp_filename_right).is_file()):
        raise FileNotFoundError('file not found: {fname}'.format(fname=inp_filename_right))
    
    data_left = None
    data_right = None
    with open(inp_filename_left) as f_l:
        with open(inp_filename_right) as f_r:
            data_left = json.load(f_l)
            data_right = json.load(f_r)
    
    print('{script_name}: script started at {dt}'.format(dt=time_start,script_name=script_name))

    result = find_diff(data_left,data_right,diff_config)
    
    result_json = json.dumps(result, indent=4)

    print('{script_name}: saving as "{fname}"'.format(fname=result_final_fname,script_name=script_name))
    with open(result_final_fname, "w") as outfile:
        outfile.write(result_json)

    time_finish = datetime.now()
    print('{script_name}: finished at {dt} (elapsed {duration})'.format(dt=time_finish,duration=time_finish-time_start,script_name=script_name))



if __name__ == '__main__':
    entry_point({'arglist_strict':True})
