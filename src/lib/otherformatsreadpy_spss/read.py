from pathlib import Path
import re
import argparse
import json
from datetime import datetime, timezone

import pandas as pd



    # if __name__ == '__main__':
    #     # run as a program
    #     from lib.markitdown.src.markitdown._markitdown import MarkItDown
    # elif '.' in __name__:
    #     # package
    #     from .lib.markitdown.src.markitdown._markitdown import MarkItDown
    # else:
    #     # included with no parent package
    #     from lib.markitdown.src.markitdown._markitdown import MarkItDown




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
    "sections": [
        {
            "name": "variables",
            "columns": ["name","label"],
            "content": []
        },
        {
            "name": "data",
            "columns": [],
            "content": []
        }
    ]
}
'''

def read(file_data):

    inp_file = file_data['filename']

    result = json.loads(JSON_TEMPLATE)
    
    result['source_file']='{f}'.format(f=inp_file)
    result['report_datetime_utc']='{f}'.format(f=(datetime.now()).astimezone(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),)
    result['report_datetime_local']='{f}'.format(f=(datetime.now()).strftime('%Y-%m-%dT%H:%M:%SZ'))

    df = pd.read_spss(inp_file)
    df_mdata = df.attrs

    result_report_scheme = result['report_scheme']
    result_report_properties = result['source_file_metadata']
    result_section_variables = result['sections'][0]
    result_section_data = result['sections'][1]
    result_variables = result_section_variables['content']
    result_data = result_section_data['content']

    for attr_name, attr_value in df_mdata.items():
        if attr_name in ['column_names''column_labels','column_names_to_label']:
            # skip these
            continue
        attr_value_clean = '{v}'.format(v=attr_value)
        if isinstance(attr_value,dict) or isinstance(attr_value,list):
            # attr_value_clean = '[ ' + ', '.join([m for m in attr_value]) + ' ]'
            attr_value_clean = json.dumps(attr_value)
        result_report_properties.append({'name':attr_name,'value':attr_value_clean})

    for col in df.columns:
        col_txt = '{t}'.format(t=col)
        col_name = col_txt
        col_label = df_mdata['column_names_to_labels'][col_txt]
        result_report_scheme['columns'].append(col_name)
        result_report_scheme['column_headers'][col_name] = col_label
        result_section_data['columns'].append(col_name)
        result_variables.append({'name':col_name,'label':col_label})

    for casenumber in range(0,len(df)):
        row = df.iloc[casenumber,]
        result_row = {}
        for col in df.columns:
            result_row['{c}'.format(c=col)] = row[col]
        result_data.append( result_row )

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
    parser.add_argument(
        '--config-read-variables',
        help='Config option: include info about the variables',
        type=str,
        required=False
    )
    parser.add_argument(
        '--config-read-data',
        help='Config option: include data (can be slow, or very slow, even on smallest projects)',
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

    print('reading file: opening {fname}, script started at {dt}'.format(dt=time_start,fname=inp_file))

    data = read({'filename':inp_file})

    result_json_fname = ( Path(inp_file).parents[0] / '{basename}{ext}'.format(basename=Path(inp_file).name,ext='.json') if Path(inp_file).is_file() else re.sub(r'^\s*?(.*?)\s*?$',lambda m: '{base}{added}'.format(base=m[1],added='.json'),'{path}'.format(path=inp_file)) )
    print('reading file: saving as "{fname}"'.format(fname=result_json_fname))
    outfile = open(result_json_fname, 'w')
    outfile.write(json.dumps(data, indent=4))

    time_finish = datetime.now()
    print('reading file: finished at {dt} (elapsed {duration})'.format(dt=time_finish,duration=time_finish-time_start))

if __name__ == '__main__':
    entry_point({'arglist_strict':True})
