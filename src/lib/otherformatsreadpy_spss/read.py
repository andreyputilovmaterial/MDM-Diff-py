from pathlib import Path
import re
import argparse
import json
from datetime import datetime, timezone

import pandas as pd



if __name__ == '__main__':
    # run as a program
    import helper_utility_performancemonitor
elif '.' in __name__:
    # package
    from . import helper_utility_performancemonitor
else:
    # included with no parent package
    import helper_utility_performancemonitor


pyreadstat = None
import_error = None
try:
    import pyreadstat
except Exception as e:
    import_error = e


CONFIG_ATTRS_NOTPRINTININTRO = [
    'column_names',
    'column_labels',
    'column_names_to_labels',
    'variable_value_labels',
    'variable_to_label',
    'value_labels',
    'original_variable_types',
    'readstat_variable_types',
    'variable_storage_width',
    'variable_display_width',
    'variable_alignment',
    'variable_measure',
    'missing_ranges',
    'missing_user_values',
    'mr_sets',
]



JSON_TEMPLATE = r'''
{
    "report_type": "SPSS",
    "source_file": "insert",
    "report_datetime_utc": "insert",
    "report_datetime_local": "insert",
    "source_file_metadata": [],
    "report_scheme": {
        "columns": [
            "name"
        ],
        "column_headers": {
            "name": "Data record ID"
        },
        "flags": [ "data-type:spss" ]
    },
    "sections": []
}
'''

def read(file_data,config={}):
    def find_column_label(name,label,config):
        display_style = None
        if 'display_label_style' in config and config['display_label_style']:
            display_style = config['display_label_style']
        else:
            display_style = 'name'
        if display_style=='name':
            return '{variable}'.format(variable=name)
        elif display_style=='label':
            return '{descr}'.format(descr=label)
        elif display_style=='combination':
            return '{variable}: {descr}'.format(variable=name,descr=label)
        else:
            raise Exception('Unrecognized --display-label-style option: {s}'.format(s=display_style))
    def sanitize_name(s):
        if s==0:
            return '0'
        if not s:
            return ''
        s = '{s}'.format(s=s)
        s = re.sub(r'^\s*','',re.sub(r'\s*$','',s,flags=re.I|re.DOTALL),flags=re.I|re.DOTALL)
        s = s.lower()
        return s

    inp_file = file_data['filename']

    result = json.loads(JSON_TEMPLATE)
    
    result['source_file']='{f}'.format(f=inp_file)
    result['report_datetime_utc']='{f}'.format(f=(datetime.now()).astimezone(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),)
    result['report_datetime_local']='{f}'.format(f=(datetime.now()).strftime('%Y-%m-%dT%H:%M:%SZ'))

    result_report_scheme = result['report_scheme']
    result_report_properties = result['source_file_metadata']
    result_section_variables = None
    result_section_value_labels = None
    result_section_data = None
    if 'read_variables' in config and config['read_variables']:
        result['sections'].append({'name':'variables','columns':['name','label'],'column_headers':{'name':'Variable Name','label':'Variable Label'},'content':[]})
        result_section_variables = result['sections'][-1]
    if 'read_value_labels' in config and config['read_value_labels']:
        result['sections'].append({'name':'value labels','columns':['name','label'],'column_headers':{'name':'Analysis Value','label':'Category Label'},'content':[]})
        result_section_value_labels = result['sections'][-1]
    if 'read_data' in config and config['read_data']:
        result['sections'].append({'name':'data','columns':['name'],'column_headers':{'name':'Data Record ID'},'content':[]})
        result_section_data = result['sections'][-1]
    result_variables = result_section_variables['content'] if result_section_variables else None
    result_value_labels = result_section_value_labels['content'] if result_section_value_labels else None
    result_data = result_section_data['content'] if result_section_data else None
    id_key = None
    if result_section_data:
        id_key = sanitize_name(config['id_key']) if 'id_key' in config else None
        if not id_key:
            raise Exception('ID key not provided but --config-read-data is set: we need an ID to read data. Please provide SPSS variable name used as an ID with --id-key option')

    print('reading spss...')
    # df = pd.read_spss(inp_file)
    # df_mdata = df.attrs
    if import_error:
        raise import_error
    df, spss_metadata = pyreadstat.read_sav(inp_file) if 'read_data' in config and config['read_data'] else pyreadstat.read_sav(inp_file,metadataonly=True)
    df_mdata = spss_metadata.__dict__
    print('done, working on it...')

    print('parsing metadata...')
    for attr_name, attr_value in df_mdata.items():
        if attr_name in CONFIG_ATTRS_NOTPRINTININTRO or attr_name[:len('readstat_')]=='readstat_':
            # skip these
            continue
        attr_value_clean = '{v}'.format(v=attr_value)
        if isinstance(attr_value,dict) or isinstance(attr_value,list):
            # attr_value_clean = '[ ' + ', '.join([m for m in attr_value]) + ' ]'
            attr_value_clean = json.dumps(attr_value)
            if len(attr_value_clean)>64:
                attr_value_clean = attr_value_clean[:63]+'...'
        result_report_properties.append({'name':attr_name,'value':attr_value_clean})

    if result_section_value_labels:
        result_value_labels_groups_check = []
        for variable_name, cat_data in df_mdata['variable_value_labels'].items():
            for cat_value_value, cat_label in cat_data.items():
                # item_name = '{variable_name}.Values[{cat_name}]'.format(variable_name=variable_name,cat_name=cat_value_value)
                item_name = '{variable_name}{sep}{cat_name}'.format(variable_name=variable_name,cat_name=cat_value_value,sep='\t')
                parent_group_name = '{variable_name}'.format(variable_name=variable_name)
                item_label = cat_label
                if not parent_group_name in result_value_labels_groups_check:
                    result_value_labels.append({'name':parent_group_name,'label':''})
                    result_value_labels_groups_check.append(parent_group_name)
                result_value_labels.append({'name':item_name,'label':item_label})

    spss_variables = [sanitize_name(v) for v in df.columns]
    # (done)) make var names case-insesitive? Translate to lowercase maybe?

    if result_section_data:
        # note: id_key is lowercased when read from config (top of this fn) and spss_variables are lowercased when grabbing from df.columns
        # so we are comparing lower to lower
        if id_key in spss_variables:
            id_key = [c for c in df.columns][spss_variables.index(id_key)]
        else:
            raise Exception('ID Key: SPSS variable with the given name is not found: "{s}"'.format(s=id_key))
        result_section_data['column_headers']['name'] = 'Data Record ID ({s})'.format(s=id_key)
    
    dict_attr_name_translate = {}
    if 'name' in spss_variables and id_key!='name':
        add_count = 1
        name_corrected = 'name'+''.join(['_']*add_count)
        while name_corrected in spss_variables:
            add_count = add_count + 1
            name_corrected = 'name'+''.join(['_']*add_count)
        dict_attr_name_translate['name'] = name_corrected

    for col_txt in df.columns:
        spss_var_name = col_txt
        spss_var_label = df_mdata['column_names_to_labels'][spss_var_name]
        column_name = sanitize_name(spss_var_name) if not sanitize_name(col_txt) in dict_attr_name_translate else dict_attr_name_translate[sanitize_name(col_txt)]
        column_label = find_column_label(spss_var_name,spss_var_label,config)
        if result_section_data:
            result_report_scheme['columns'].append(column_name)
            result_report_scheme['column_headers'][column_name] = column_label
            result_section_data['columns'].append(column_name)
            result_section_data['column_headers'][column_name] = column_label
        if result_section_variables:
            result_variables.append({'name':spss_var_name,'label':spss_var_label})

    if result_section_data:
        print('reading data...')
        performance_counter = iter(helper_utility_performancemonitor.PerformanceMonitor(config={
            'total_records': len(df),
            'report_frequency_records_count': 3,
            'report_frequency_timeinterval': 9,
            'report_text_pipein': 'reading case data',
        }))
        for casenumber in range(0,len(df)):
            row = df.iloc[casenumber,]
            next(performance_counter)
            result_row = {
                'name': row[id_key]
            }
            for col in df.columns:
                col_txt = sanitize_name(col)
                spss_data_col = col
                result_record_col = col_txt if not col_txt in dict_attr_name_translate else dict_attr_name_translate[col_txt]
                result_row[result_record_col] = row[spss_data_col]
            result_data.append( result_row )
    
    print('done')

    return result


def entry_point(config={}):
    def arg_str2bool(value):
        if isinstance(value,bool):
            return value
        elif isinstance(value,int) or isinstance(value,float):
            return not not value
        elif re.match(r'^\s*?$',value,flags=re.I|re.DOTALL):
            return False
        elif re.match(r'^\s*?(?:true|1|yes)\s*?$',value,flags=re.I|re.DOTALL):
            return True
        elif re.match(r'^\s*?(?:false|0|no)\s*?$',value,flags=re.I|re.DOTALL):
            return False
        else:
            try:
                value = int(value)
                return not not value
            except:
                pass
            try:
                value = float(value)
                return not not value
            except:
                pass
                return not not value
    time_start = datetime.now()
    parser = argparse.ArgumentParser(
        description="Create a JSON suitable for mdmtoolsap tool, reading a file as spss",
        prog='mdmtoolsap --program read_spss'
    )
    parser.add_argument(
        '--inpfile',
        help='Input file',
        type=str,
        required=True
    )
    parser.add_argument(
        '--config-read-variables',
        help='Config option: include info about the variables',
        type=arg_str2bool,
        default=True,
        required=False
    )
    parser.add_argument(
        '--config-read-value-labels',
        help='Config option: include info about the variables',
        type=arg_str2bool,
        default=True,
        required=False
    )
    parser.add_argument(
        '--config-read-data',
        help='Config option: include data (can be slow, or very slow, even on smallest projects)',
        type=arg_str2bool,
        default=False,
        required=False
    )
    parser.add_argument(
        '--id-key',
        help='SPSS variable used as an ID',
        type=str,
        required=False
    )
    parser.add_argument(
        '--config-display-label-style',
        help='Holds what to show: variable name, label, or a combination. Possible values are "name", "label", "combination"',
        type=str,
        required=False
    )
    args = None
    args_rest = None
    if( ('arglist_strict' in config) and (not config['arglist_strict']) ):
        args, args_rest = parser.parse_known_args()
    else:
        args = parser.parse_args()
    
    inp_file = Path(args.inpfile)
    inp_file = '{inp_file}'.format(inp_file=inp_file.resolve())
    if not(Path(inp_file).is_file()):
        raise FileNotFoundError('file not found: {fname}'.format(fname=inp_file))
    
    config_spss_reader = {
        'read_variables': args.config_read_variables,
        'read_value_labels': args.config_read_value_labels,
        'read_data': args.config_read_data,
    }
    if args.id_key:
        config_spss_reader['id_key'] = args.id_key
    if args.config_display_label_style:
        config['display_label_style'] = args.config_display_label_style
        if not config['display_label_style'] in ['name','label','combination']:
            raise Exception('--config-display-label-style param can only be of one of the following: "name", "label", "combination", but received "{s}"'.format(s=config['display_label_style']))

    print('reading file: opening {fname}, script started at {dt}'.format(dt=time_start,fname=inp_file))

    data = read({'filename':inp_file},config=config_spss_reader)

    result_json_fname = ( Path(inp_file).parents[0] / '{basename}{ext}'.format(basename=Path(inp_file).name,ext='.json') if Path(inp_file).is_file() else re.sub(r'^\s*?(.*?)\s*?$',lambda m: '{base}{added}'.format(base=m[1],added='.json'),'{path}'.format(path=inp_file)) )
    print('reading file: saving as "{fname}"'.format(fname=result_json_fname))
    outfile = open(result_json_fname, 'w')
    outfile.write(json.dumps(data, indent=4))

    time_finish = datetime.now()
    print('reading file: finished at {dt} (elapsed {duration})'.format(dt=time_finish,duration=time_finish-time_start))

if __name__ == '__main__':
    entry_point({'arglist_strict':True})
