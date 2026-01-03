# import os, time, re, sys
import os
from datetime import datetime, timezone
# from dateutil import tz
import argparse
from pathlib import Path
import re
import json
import sys # for error reporting, to print to stderr



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




CONFIG_NUM_COLUMNS_CONSIDERED_DIFFICULT = 1000
CONFIG_NUM_ROWS_CONSIDERED_DIFFICULT = 3000



def find_diff(data_left,data_right,config):

    datetime_start = datetime.now()
    config_default = {
        'format': 'sidebyside'
    }
    config = {**config_default,**config}
    config['verbose_prep_logging'] = False
    try:
        if len(data_left['report_scheme']['columns'])>CONFIG_NUM_COLUMNS_CONSIDERED_DIFFICULT or len(data_right['report_scheme']['columns'])>CONFIG_NUM_COLUMNS_CONSIDERED_DIFFICULT:
            config['verbose_prep_logging'] = True
    except:
        pass
    if config['verbose_prep_logging']:
       print('preparation...')
    if config['verbose_prep_logging']:
       print('config...')
    config['format'] = config['format']
    config_diff_format = None
    if config['format']=='sidebyside':
        config_diff_format = 'sidebyside'
    elif config['format']=='sidebyside_distant':
        config_diff_format = 'sidebyside'
    elif config['format']=='combined':
        config_diff_format = 'combined'
    else:
        raise Exception('diff format=="{fmt}": not supported, or not implemented'.format(fmt=config['format']))
    
    # if config_diff_format=='combined':
    #     raise Exception('diff format=="combined": not implemented yet')

    if config['verbose_prep_logging']:
       print('find combined list of columns...')
    columns_list_combined_global = [
        'flagdiff', 'name'
    ]
    data_columns_global_left = data_left['report_scheme']['columns']
    data_columns_global_right = data_right['report_scheme']['columns']
    columns_list_check_global = [ col for col in helper_diff_wrappers.diff_make_combined_list(data_columns_global_left,data_columns_global_right) if not re.match(r'^\s*?name\s*?$',col,flags=re.I) ]
    if config['format']=='sidebyside':
        # add left and right, left and right...
        for col in columns_list_check_global:
            columns_list_combined_global.append('{basename}{suffix}'.format(basename=col,suffix='_left'))
            columns_list_combined_global.append('{basename}{suffix}'.format(basename=col,suffix='_right'))
    elif config['format']=='sidebyside_distant':
        # add all left, then all right
        for col in columns_list_check_global:
            columns_list_combined_global.append('{basename}{suffix}'.format(basename=col,suffix='_left'))
        for col in columns_list_check_global:
            columns_list_combined_global.append('{basename}{suffix}'.format(basename=col,suffix='_right'))
    elif config['format']=='combined':
        # no left and right, just columns that contain diffs with added parts and removed
        for col in columns_list_check_global:
            columns_list_combined_global.append('{basename}{suffix}'.format(basename=col,suffix=''))
    else:
        raise Exception('diff format=="{fmt}": not supported, or not implemented'.format(fmt=config['format']))
    
    column_headers_combined = {'name':'Item name','flagdiff':'Diff flag'}
    for key in dict.keys({**data_right['report_scheme']['column_headers'],**data_left['report_scheme']['column_headers']}):
        if key in data_left['report_scheme']['column_headers']:
            column_headers_combined['{name}'.format(name=key)] = '{basename}'.format(basename=data_left['report_scheme']['column_headers'][key])
            column_headers_combined['{name}_left'.format(name=key)] = '{basename} (Left file)'.format(basename=data_left['report_scheme']['column_headers'][key])
        if key in data_right['report_scheme']['column_headers']:
            if not( '{name}'.format(name=key) in column_headers_combined ):
                column_headers_combined['{name}'.format(name=key)] = '{basename}'.format(basename=data_right['report_scheme']['column_headers'][key])
            column_headers_combined['{name}_right'.format(name=key)] = '{basename} (Right file)'.format(basename=data_right['report_scheme']['column_headers'][key])
    if config['verbose_prep_logging']:
       print('flags...')
    # flags_list_combined = helper_diff_wrappers.diff_make_combined_list( data_left['report_scheme']['flags'] if 'flags' in data_left['report_scheme'] else [], data_right['report_scheme']['flags'] if 'flags' in data_right['report_scheme'] else [] )
    flags_list_combined = [ 'data-type:diff' ] + [ flag for flag in (data_left['report_scheme']['flags'] if 'flags' in data_left['report_scheme'] else []) if flag in (data_right['report_scheme']['flags'] if 'flags' in data_right['report_scheme'] else []) ] + [ '{prefix}{flag}'.format(prefix='diff_source_left:',flag=flag) for flag in (data_left['report_scheme']['flags'] if 'flags' in data_left['report_scheme'] else []) ] + [ '{prefix}{flag}'.format(prefix='diff_source_right:',flag=flag) for flag in (data_right['report_scheme']['flags'] if 'flags' in data_right['report_scheme'] else []) ]
    section_list_combined = helper_diff_wrappers.diff_make_combined_list( [ item['name'] for item in data_left['sections']], [ item['name'] for item in data_right['sections']])

    if config['verbose_prep_logging']:
       print('final config...')
    if not ('config_use_hierarchical_name_structure' in config):
        if 'data-type:mdd' in flags_list_combined:
            config['config_use_hierarchical_name_structure'] = True
        elif 'data-type:excel' in flags_list_combined:
            config['config_use_hierarchical_name_structure'] = False
        elif 'data-type:spss' in flags_list_combined:
            config['config_use_hierarchical_name_structure'] = True
    if ('config_use_hierarchical_name_structure' in config) and config['config_use_hierarchical_name_structure']:
        if 'data-type:mdd' in flags_list_combined:
            config['config_hierarchical_name_separator'] = '.'
        elif 'data-type:spss' in flags_list_combined:
            config['config_hierarchical_name_separator'] = '\t'
        elif 'data-type:excel' in flags_list_combined:
            # config['config_hierarchical_name_separator'] = ' ---->>>> '
            raise Exception('excel with groups in item names? are you sure? please provide a separator!')
        else:
            config['config_hierarchical_name_separator'] = config['config_use_hierarchical_name_structure']


    result = {
        'report_type': 'diff',
        'source_left': '{path}'.format(path=config['inp_filename_left']),
        'source_right': '{path}'.format(path=config['inp_filename_right']),
        'report_datetime_utc': datetime_start.astimezone(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'report_datetime_local': datetime_start.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'source_file_metadata': [
            { 'name': 'source_left', 'value': '{path}'.format(path=config['inp_filename_left']) },
            { 'name': 'source_right', 'value': '{path}'.format(path=config['inp_filename_right']) },
        ],
        'report_scheme': {
            'columns': columns_list_combined_global,
            'column_headers': column_headers_combined,
            'flags': flags_list_combined
        },
        'sections': [],
    }
    if config['verbose_prep_logging']:
       print('go!')
    for section_name in section_list_combined:
        try:
            
            print('== processing section {name} =='.format(name=section_name))
            
            file_l_sections_allmatches = [ section for section in data_left['sections'] if section['name']==section_name ]
            file_r_sections_allmatches = [ section for section in data_right['sections'] if section['name']==section_name ]
            file_l_section = file_l_sections_allmatches[0] if len(file_l_sections_allmatches)>0 else {}
            file_r_section = file_r_sections_allmatches[0] if len(file_r_sections_allmatches)>0 else {}
            file_l_sectiondata_as_list = file_l_section['content'] if 'content' in file_l_section else []
            file_r_sectiondata_as_list = file_r_section['content'] if 'content' in file_r_section else []
            def fail_no_name_attr():
                raise Exception('Data must include "name" column that is used as an ID, we can\'t compare records without it. Exit.')
            file_l_sectiondata = {}
            for item in file_l_sectiondata_as_list:
                name = item['name'] if 'name' in item else fail_no_name_attr()
                counter = 2
                while name in file_l_sectiondata:
                    name = '{part_existing}{part_added}'.format(part_existing=item['name'],part_added='_duplicate({d})'.format(d=counter))
                    counter = counter + 1
                file_l_sectiondata[name] = item
            file_r_sectiondata = {}
            for item in file_r_sectiondata_as_list:
                name = item['name'] if 'name' in item else fail_no_name_attr()
                counter = 2
                while name in file_r_sectiondata:
                    name = '{part_existing}{part_added}'.format(part_existing=item['name'],part_added='_duplicate({d})'.format(d=counter))
                    counter = counter + 1
                file_r_sectiondata[name] = item
            rows_l = [ name for name in file_l_sectiondata.keys() ]
            rows_r = [ name for name in file_r_sectiondata.keys() ]
            
            section_other_props = helper_diff_wrappers.finddiff_values_general_formatcombined( {**file_l_section,'content':None}, {**file_r_section,'content':None} )
            # if 'columns' in file_l_section or 'columns' in file_r_section:
            #     section_other_props['columns'] = [ column for column in helper_diff_wrappers.diff_make_combined_list(file_l_section['columns'] if 'columns' in file_l_section else [],file_r_section['columns'] if 'columns' in file_r_section else []) ]

            columns_list_check = []
            data_columns_left = file_l_section['columns'] if 'columns' in file_l_section else data_columns_global_left
            data_columns_right = file_r_section['columns'] if 'columns' in file_r_section else data_columns_global_right
            columns_list_combined = [
                'flagdiff', 'name'
            ]
            if not config['verbose_prep_logging'] and ( (len(data_columns_left)>CONFIG_NUM_COLUMNS_CONSIDERED_DIFFICULT) or (len(data_columns_right)>CONFIG_NUM_COLUMNS_CONSIDERED_DIFFICULT) ):
                config['verbose_prep_logging'] = True
            if config['verbose_prep_logging']:
                print('compiling combined column list...')
            columns_list_check = [ col for col in helper_diff_wrappers.diff_make_combined_list(data_columns_left,data_columns_right) if not re.match(r'^\s*?name\s*?$',col,flags=re.I) ]
            if config['format']=='sidebyside':
                # add left and right, left and right...
                for col in columns_list_check:
                    columns_list_combined.append('{basename}{suffix}'.format(basename=col,suffix='_left'))
                    columns_list_combined.append('{basename}{suffix}'.format(basename=col,suffix='_right'))
            elif config['format']=='sidebyside_distant':
                # add all left, then all right
                for col in columns_list_check:
                    columns_list_combined.append('{basename}{suffix}'.format(basename=col,suffix='_left'))
                for col in columns_list_check:
                    columns_list_combined.append('{basename}{suffix}'.format(basename=col,suffix='_right'))
            elif config['format']=='combined':
                # no left and right, just columns that contain diffs with added parts and removed
                for col in columns_list_check:
                    columns_list_combined.append('{basename}{suffix}'.format(basename=col,suffix=''))
            else:
                raise Exception('diff format=="{fmt}": not supported, or not implemented'.format(fmt=config['format']))
            section_other_props['columns'] = columns_list_combined
            if 'column_headers' in section_other_props:
                column_headers_left = (file_l_section['column_headers'] or {}) if 'column_headers' in file_l_section else {}
                column_headers_right = (file_r_section['column_headers'] or {}) if 'column_headers' in file_r_section else {}
                section_other_props['column_headers'] = { **column_headers_left, **column_headers_right }
                column_headers = section_other_props['column_headers']
                for col_id, lab in ({**column_headers}).items():
                    lab_left = (column_headers_left[col_id] if col_id in column_headers_left else lab) or lab
                    lab_right = (column_headers_right[col_id] if col_id in column_headers_right else lab) or lab
                    section_other_props['column_headers']['{n}_left'.format(n=col_id)] = '{basename} (Left file)'.format(basename=lab_left)
                    section_other_props['column_headers']['{n}_right'.format(n=col_id)] = '{basename} (Right file)'.format(basename=lab_right)

            result_this_section = []

            section_changed = False
            rows_changed = 0
            row_count = 0
            
            if not config['verbose_prep_logging'] and ( (len(rows_l)>CONFIG_NUM_ROWS_CONSIDERED_DIFFICULT) or (len(rows_r)>CONFIG_NUM_ROWS_CONSIDERED_DIFFICULT) ):
                config['verbose_prep_logging'] = True
            if config['verbose_prep_logging']:
                print('finding list of items that were added or removed...')
            if ('config_use_hierarchical_name_structure' in config and config['config_use_hierarchical_name_structure']):
                # add root element
                rows_l = rows_l if '' in rows_l else ['']+rows_l
                rows_r = rows_r if '' in rows_r else ['']+rows_r
            # confirm that row names are unique
            
            report_rows_diff = helper_diff_wrappers.finddiff_row_names_respecting_groups( rows_l, rows_r, delimiter=(config['config_hierarchical_name_separator'] if ('config_use_hierarchical_name_structure' in config and config['config_use_hierarchical_name_structure']) else None) )
            
            performance_counter = iter(helper_utility_wrappers.PerformanceMonitor(config={
                'total_records': len(report_rows_diff),
                'report_frequency_records_count': 150,
                'report_frequency_timeinterval': 6
            }))
            if config['verbose_prep_logging']:
                print('calculating diffs within each row...')
            for row_diff_item in report_rows_diff:
                try:
                    
                    row_name = row_diff_item.line
                    next(performance_counter)
                    row = {}
                    row['name'] = row_name

                    flag = '???'

                    row_changed = False

                    if row_diff_item.flag == 'keep':
                        flag = '(keep)'
                    elif( (row_name in rows_l) and (row_name in rows_r) ):
                        if row_diff_item.flag == 'remove':
                            flag = '(moved from here)'
                        elif row_diff_item.flag == 'insert':
                            flag = '(moved here)'
                        else:
                            raise Exception('Please check diff flag!!!')
                        row_changed = True
                    elif( row_name in rows_l ):
                        flag = '(removed)'
                        row_changed = True
                    elif( row_name in rows_r ):
                        flag = '(added)'
                        row_changed = True
                    row['flagdiff'] = flag
                    file_l_rowdata = {}
                    file_r_rowdata = {}
                    if( ( (row_name in rows_l) and (row_name in rows_r) ) and (row_diff_item.flag == 'remove') and ('config_do_not_show_content_rows_moved_from' in config and config['config_do_not_show_content_rows_moved_from']) ):
                        # skip for rows moved at their old position
                        pass
                    else:
                        if( row_name in rows_l ):
                            file_l_rowdata = file_l_sectiondata[row_name] if row_name in file_l_sectiondata else {}
                        if( row_name in rows_r ):
                            file_r_rowdata = file_r_sectiondata[row_name] if row_name in file_r_sectiondata else {}
                    for col in columns_list_check:

                        file_l_coldata = file_l_rowdata[col] if col in file_l_rowdata else None
                        file_r_coldata = file_r_rowdata[col] if col in file_r_rowdata else None

                        col_changed = False

                        if config_diff_format == 'sidebyside':

                            result_this_col_left, result_this_col_right = helper_diff_wrappers.finddiff_values_general_formatsidebyside( file_l_coldata, file_r_coldata )
                            
                            if helper_diff_wrappers.check_if_includes_addedremoved_marker(result_this_col_left) or helper_diff_wrappers.check_if_includes_addedremoved_marker(result_this_col_right):
                                col_changed = True
                            row['{col_name}{suffix}'.format(col_name = col,suffix='_left')] = result_this_col_left
                            row['{col_name}{suffix}'.format(col_name = col,suffix='_right')] = result_this_col_right

                        elif config_diff_format == 'combined':

                            result_this_col_combined = helper_diff_wrappers.finddiff_values_general_formatcombined( file_l_coldata, file_r_coldata )
                            
                            if helper_diff_wrappers.check_if_includes_addedremoved_marker(result_this_col_combined):
                                col_changed = True
                            row['{col_name}{suffix}'.format(col_name = col,suffix='')] = result_this_col_combined

                        else:
                            raise Exception('other diff format tyhat is not supported: {fmt}'.format(fmt=config_diff_format))
                        
                        if col_changed:
                            row_changed = True
                    if row_changed:
                        section_changed = True
                        rows_changed = rows_changed + 1
                    row_count = row_count + 1
                    if 'config_skip_rows_nochange' in config and config['config_skip_rows_nochange']:
                        if row_changed:
                            result_this_section.append(row)
                    else:
                        result_this_section.append(row)
                except Exception as e:
                    print('ERROR: something happened when processing row {name}'.format(name=row_name),file=sys.stderr)
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
                'title': section_title,
                **section_other_props,
                'name': section_name,
                'changed': section_changed,
                'statistics': [
                    { 'name': 'something changed', 'value': 'true' if section_changed else 'false' },
                    { 'name': 'rows total', 'value': row_count },
                    { 'name': 'rows changed', 'value': rows_changed },
                ],
                'content': result_this_section
            }
            if 'config_skip_rows_nochange' in config and config['config_skip_rows_nochange']:
                if not section_changed:
                    cols = [ col for col in columns_list_combined_global if not (col in ['name','flagdiff'])]
                    zero_column_name = cols[0] if len(cols)>0 else 'label'
                    section_add['content'] = [
                        {'name':'',zero_column_name:'(There is no difference to show)'}
                    ]
            result['sections'].append(section_add)
        except Exception as e:
            print('ERROR: something happened when processing section {name}'.format(name=section_name),file=sys.stderr)
            raise e
    return result


def make_diff_fname_part(fname_l,fname_r):
    fname_l = '{fname_l}'.format(fname_l=fname_l)
    fname_r = '{fname_r}'.format(fname_r=fname_r)
    # fname_l = list(fname_l)
    # fname_r = list(fname_r)
    fname_l = helper_diff_wrappers.text_split_words(fname_l)
    fname_r = helper_diff_wrappers.text_split_words(fname_r)
    diff_temp = helper_diff_wrappers.diff_raw( fname_l, fname_r )
    # add a dummy element for trailing part
    diff_temp.append({
        'lhs': {
            'at': len(fname_l),
            'add': 0,
            'del': 0
        },
        'rhs': {
            'at': len(fname_r),
            'add': 0,
            'del': 0
        }
    })
    # go
    result = ''
    last_index = 0
    for diff_entry in diff_temp:
        part_l_keep_start = last_index
        part_l_keep_end = diff_entry['lhs']['at']
        part_r_keep_shift = diff_entry['rhs']['at'] - diff_entry['lhs']['at']
        part_l_del_start = diff_entry['lhs']['at']
        part_l_del_end = diff_entry['lhs']['at'] + diff_entry['lhs']['del']
        part_r_add_start = diff_entry['rhs']['at']
        part_r_add_end = diff_entry['rhs']['at'] + diff_entry['rhs']['add']
        last_index = diff_entry['lhs']['at'] + diff_entry['lhs']['del']
        # has_part_kept = False
        # has_part_added = False
        # has_part_removed = False
        part_kept = ''
        part_added = ''
        part_removed = ''
        for i in range(part_l_keep_start,part_l_keep_end):
            # no change - names are good
            part_kept = part_kept + fname_l[i]
            # has_part_kept = True
        for i in range(part_l_del_start,part_l_del_end):
            # removed
            part_removed = part_removed + fname_l[i]
            # has_part_removed = True
        for i in range(part_r_add_start,part_r_add_end):
            # added
            part_added = part_added + fname_r[i]
            # has_part_added = True
        result = result + ('-' if ((len(part_kept)>0) and (len(result)>0)) else '') + part_kept
        result = result + ('-' if ((len(part_removed)>0) and (len(result)>0)) else '') + part_removed
        result = result + ('-' if ((len(part_added)>0) and (len(result)>0)) else '') + part_added
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
        help='Format: print results as 2 separate columns, or combine; possible values: sidebyside (default), sidebyside_distant, combined',
        type=str,
        required=False
    )
    parser.add_argument(
        '--config-skip-rows-nochange',
        help='Special flag to indicate that we should not add all rows to sections where nothing changed; I prefer to have this set to false in MDD - if nothing changed in shared lists we prefer to still see shared lists; but I prefer to have this set to true for Excel - having so many rows is unnecessary',
        action='store_true',
        required=False
    )
    parser.add_argument(
        '--config-do-not-show-content-rows-moved-from',
        help='Special flag to indicate that we should not print contents of "moved from" rows',
        action='store_true',
        required=False
    )
    parser.add_argument(
        '--config-use-hierarchical-name-structure',
        help='Special flag to indicate that we should not print contents of "moved from" rows',
        action='store_true',
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

    diff_format = 'sidebyside'
    if args.cmp_format:
        diff_format = args.cmp_format
        fmts_allowed = ['sidebyside','sidebyside_distant','combined']
        if not (diff_format in fmts_allowed):
            raise Exception('diff: unsupported config option: diff format: "{fmt}"; you can only use [ {allowed} ]'.format(fmt=diff_format,alowed=', '.join(fmts_allowed)))

    diff_config = {
        'format': diff_format,
        'inp_filename_left': inp_filename_left,
        'inp_filename_right': inp_filename_right
    }
    if args.config_skip_rows_nochange:
        diff_config['config_skip_rows_nochange'] = True
    if args.config_do_not_show_content_rows_moved_from:
        diff_config['config_do_not_show_content_rows_moved_from'] = True
    if args.config_use_hierarchical_name_structure:
        diff_config['config_use_hierarchical_name_structure'] = True

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
        # report_filename_filepart = '{fname_prefix}{file_l}-{file_r}{fname_suffix}.json'.format(file_l=report_part_filename_left,file_r=report_part_filename_right,fname_prefix=report_filename_prefixpart,fname_suffix=report_filename_suffixpart)
        report_filename_filepart = '{fname_prefix}{diff_file_name_part_holder}{fname_suffix}.json'.format(diff_file_name_part_holder=make_diff_fname_part(report_part_filename_left,report_part_filename_right),fname_prefix=report_filename_prefixpart,fname_suffix=report_filename_suffixpart)
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
            try:
                data_left = json.load(f_l)
            except json.JSONDecodeError as e:
                # just a more descriptive message to the end user
                # can happen if the tool is started two times in parallel and it is writing to the same json simultaneously
                raise Exception('Diff: Can\'t read left file as JSON: {msg}'.format(msg=e))
            try:
                data_right = json.load(f_r)
            except json.JSONDecodeError as e:
                # just a more descriptive message to the end user
                # can happen if the tool is started two times in parallel and it is writing to the same json simultaneously
                raise Exception('Diff: Can\'t read right file as JSON: {msg}'.format(msg=e))
    
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
