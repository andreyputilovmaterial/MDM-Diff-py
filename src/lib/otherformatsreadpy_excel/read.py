from pathlib import Path
import re
import argparse
import json
from datetime import datetime, timezone

def entry_point(config={}):
    time_start = datetime.now()
    parser = argparse.ArgumentParser(
        description="Create a JSON suitable for mdmtoolsap tool, reading a file as text"
    )
    parser.add_argument(
        '--inpfile',
        help='Input file',
        required=True
    )
    args = None
    args_rest = None
    if( ('arglist_strict' in config) and (not config['arglist_strict']) ):
        args, args_rest = parser.parse_known_args()
    else:
        args = parser.parse_args()
    inp_file = Path(args.inpfile)

    print('reading Excel: opening {fname}, script started at {dt}'.format(dt=time_start,fname=inp_file))

    data = ''
    raise Exception('reading Excel: not impemented yet!')

    result_json_fname = ( Path(inp_file).parents[0] / '{basename}{ext}'.format(basename=Path(inp_file).name,ext='.json') if Path(inp_file).is_file() else re.sub(r'^\s*?(.*?)\s*?$',lambda m: '{base}{added}'.format(base=m[1],added='.json'),'{path}'.format(path=inp_file)) )
    outfile = open(result_json_fname, 'w')
    outfile.write(json.dumps(data))

    time_finish = datetime.now()
    print('reading Excel: finished at {dt} (elapsed {duration})'.format(dt=time_finish,duration=time_finish-time_start))

if __name__ == '__main__':
    entry_point({'arglist_strict':True})
