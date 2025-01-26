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




JSON_TEMPLATE = r'''
{
    "report_type": "SPSS",
    "source_file": "insert",
    "report_datetime_utc": "insert",
    "report_datetime_local": "insert",
    "source_file_metadata": [],
    "report_scheme": {
        "columns": [
            ""
        ],
        "column_headers": {
            "": " "
        },
        "flags": [ "data-type:spss" ]
    },
    "sections": []
}
'''

def read(file_data,config={}):

    inp_file = file_data['filename']

    result = json.loads(JSON_TEMPLATE)
    
    result['source_file']='{f}'.format(f=inp_file)
    result['report_datetime_utc']='{f}'.format(f=(datetime.now()).astimezone(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),)
    result['report_datetime_local']='{f}'.format(f=(datetime.now()).strftime('%Y-%m-%dT%H:%M:%SZ'))

    print('reading spss...')
    df = pd.read_spss(inp_file)
    df_mdata = df.attrs

    print('done, working on it...')
    result_report_scheme = result['report_scheme']
    result_report_properties = result['source_file_metadata']
    result_section_variables = None
    result_section_value_labels = None
    result_section_data = None
    if 'read_variables' in config and config['read_variables']:
        result['sections'].append({'name':'variables','columns':['name','label'],'content':[]})
        result_section_variables = result['sections'][-1]
    if 'read_value_labels' in config and config['read_value_labels']:
        result['sections'].append({'name':'value labels','columns':['name','label'],'content':[]})
        result_section_value_labels = result['sections'][-1]
    if 'read_data' in config and config['read_data']:
        result['sections'].append({'name':'data','columns':[],'content':[]})
        result_section_data = result['sections'][-1]
    result_variables = result_section_variables['content'] if result_section_variables else None
    result_value_labels = result_section_value_labels['content'] if result_section_value_labels else None
    result_data = result_section_data['content'] if result_section_data else None

    print('reading metadata...')
    for attr_name, attr_value in df_mdata.items():
        if attr_name in [
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
        ] or attr_name[:len('readstat_')]=='readstat_':
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
        for variable_name, cat_data in df_mdata['variable_value_labels'].items():
            for cat_value_value, cat_label in cat_data.items():
                item_name = '{variable_name}.Values[{cat_name}]'.format(variable_name=variable_name,cat_name=cat_value_value)
                item_label = cat_label
                result_value_labels.append({'name':item_name,'label':item_label})

    for col in df.columns:
        col_txt = '{t}'.format(t=col)
        col_name = col_txt
        col_label = df_mdata['column_names_to_labels'][col_txt]
        result_report_scheme['columns'].append(col_name)
        result_report_scheme['column_headers'][col_name] = col_label
        if result_section_data:
            result_section_data['columns'].append(col_name)
        if result_section_variables:
            result_variables.append({'name':col_name,'label':col_label})

    if result_section_data:
        print('reading data...')
        performance_counter = iter(helper_utility_performancemonitor.PerformanceMonitor(config={
            'total_records': len(df),
            'report_frequency_records_count': 1,
            'report_frequency_timeinterval': 9,
        }))
        for casenumber in range(0,len(df)):
            row = df.iloc[casenumber,]
            next(performance_counter)
            result_row = {}
            for col in df.columns:
                result_row['{c}'.format(c=col)] = row[col]
            result_data.append( result_row )
    
    print('done')

    return result


def entry_point(config={}):
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
