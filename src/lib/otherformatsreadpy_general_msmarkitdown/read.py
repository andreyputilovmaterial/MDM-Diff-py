from pathlib import Path
import re
import argparse
import json
from datetime import datetime, timezone



did_import_fail = None

try:
    if __name__ == '__main__':
        # run as a program
        from lib.markitdown.packages.markitdown.src.markitdown._markitdown import MarkItDown
    elif '.' in __name__:
        # package
        from .lib.markitdown.packages.markitdown.src.markitdown._markitdown import MarkItDown
    else:
        # included with no parent package
        from lib.markitdown.packages.markitdown.src.markitdown._markitdown import MarkItDown
except Exception as e:
    did_import_fail = e



def read_contents(fname):
    if did_import_fail:
        raise did_import_fail
    md = MarkItDown()
    result = md.convert(fname)
    return result.text_content



JSON_TEMPLATE = r'''
{
    "report_type": "MSMarkItDown",
    "source_file": "insert",
    "report_datetime_utc": "insert",
    "report_datetime_local": "insert",
    "source_file_metadata": [],
    "report_scheme": {
        "columns": [
            "rawtextcontents"
        ],
        "column_headers": {
            "rawtextcontents": "File Contents"
        },
        "flags": [ "data-type:markitdown" ]
    },
    "sections": [
        {
            "name": "filecontents",
            "content": [
                {
                    "name": "",
                    "rawtextcontents": "insert"
                }
            ]
        }
    ]
}
'''

def read(file_data):

    inp_file = file_data['filename']

    data=json.loads(JSON_TEMPLATE)
    
    data['source_file']='{f}'.format(f=inp_file)
    data['report_datetime_utc']='{f}'.format(f=(datetime.now()).astimezone(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),)
    data['report_datetime_local']='{f}'.format(f=(datetime.now()).strftime('%Y-%m-%dT%H:%M:%SZ'))

    textfilecontents = read_contents(inp_file)

    data['sections'][0]['content'][0]['rawtextcontents'] = textfilecontents

    return data


def entry_point(config={}):
    time_start = datetime.now()
    parser = argparse.ArgumentParser(
        description="Create a JSON suitable for mdmtoolsap tool, reading a file as ms markup",
        prog='mdmtoolsap --program read_markitdown'
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
    inp_file = '{inp_file}'.format(inp_file=inp_file.resolve())
    if not(Path(inp_file).is_file()):
        raise FileNotFoundError('file not found: {fname}'.format(fname=inp_file))

    print('reading file: opening {fname}, script started at {dt}'.format(dt=time_start,fname=inp_file))

    # inp_file_obj = open(inp_file,'r',encoding='utf-8')
    # textfilecontents = inp_file_obj.read()

    data = read({'filename':inp_file})

    result_json_fname = ( Path(inp_file).parents[0] / '{basename}{ext}'.format(basename=Path(inp_file).name,ext='.json') if Path(inp_file).is_file() else re.sub(r'^\s*?(.*?)\s*?$',lambda m: '{base}{added}'.format(base=m[1],added='.json'),'{path}'.format(path=inp_file)) )
    print('reading file: saving as "{fname}"'.format(fname=result_json_fname))
    outfile = open(result_json_fname, 'w')
    outfile.write(json.dumps(data, indent=4))

    time_finish = datetime.now()
    print('read script: finished at {dt} (elapsed {duration})'.format(dt=time_finish,duration=time_finish-time_start))

if __name__ == '__main__':
    entry_point({'arglist_strict':True})
