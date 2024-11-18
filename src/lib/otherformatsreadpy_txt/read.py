from pathlib import Path
import re
import argparse
import json
from datetime import datetime, timezone




if __name__ == '__main__':
    # run as a program
    import reader_plain
    import reader_tablescripts
elif '.' in __name__:
    # package
    from . import reader_plain
    from . import reader_tablescripts
else:
    # included with no parent package
    import reader_plain
    import reader_tablescripts







def entry_point(config={}):
    # time_start = datetime.now()
    parser = argparse.ArgumentParser(
        description="Create a JSON suitable for mdmtoolsap tool, reading a file as text",
        prog='mdmtoolsap --program read_txt'
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
    inp_filename = '{f}'.format(f=inp_file)

    # print('reading file {fname}, script started at {dt}'.format(dt=time_start,fname=inp_file))

    inp_file_obj = open(inp_file,'r',encoding='utf-8')
    textfilecontents = inp_file_obj.read()

    format_detect = None
    if re.match(r'^\s*?TabScripts.*?\.mrs',inp_filename,flags=re.I):
        format_detect = 'da_tablescrips'
    elif re.match(r'^\s*?PrepDataDMS.*?\.txt',inp_filename,flags=re.I):
        format_detect = 'da_dms'

    read = None
    if format_detect=='da_tablescrips':
        read = reader_tablescripts.read
    else:
        read = reader_plain.read

    data = read(textfilecontents,{'filename':inp_filename})

    result_json_fname = ( Path(inp_file).parents[0] / '{basename}{ext}'.format(basename=Path(inp_file).name,ext='.json') if Path(inp_file).is_file() else re.sub(r'^\s*?(.*?)\s*?$',lambda m: '{base}{added}'.format(base=m[1],added='.json'),'{path}'.format(path=inp_file)) )
    outfile = open(result_json_fname, 'w')
    outfile.write(json.dumps(data))

    # time_finish = datetime.now()
    # print('MDM read script: finished at {dt} (elapsed {duration})'.format(dt=time_finish,duration=time_finish-time_start))

if __name__ == '__main__':
    entry_point({'arglist_strict':True})
