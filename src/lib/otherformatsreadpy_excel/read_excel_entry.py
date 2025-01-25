from pathlib import Path
import re
import argparse
import json
from datetime import datetime, timezone


import numpy as np # needed for correct handling of pandas types when converting to json - pandas types are based on numpy



if __name__ == '__main__':
    # run as a program
    import read_excel_lrw
    import read_excel_general
elif '.' in __name__:
    # package
    from . import read_excel_lrw
    from . import read_excel_general
else:
    # included with no parent package
    import read_excel_lrw
    import read_excel_general



def json_dump_defaulthandler(obj):
    if type(obj).__module__ == np.__name__:
        if isinstance(obj,np.ndarray):
            return obj.tolist()
        else:
            return obj.item()
    raise TypeError('Unknown type: ',type(obj))



def entry_point(config={}):
    time_start = datetime.now()
    parser = argparse.ArgumentParser(
        description="Create a JSON suitable for mdmtoolsap tool, reading a file as text",
        prog='mdmtoolsap --program read_excel'
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


    print('reading Excel: opening {fname}, script started at {dt}'.format(dt=time_start,fname=inp_file))

    data = None
    data_fetched = False
    # we don't know if the excel is following format of lrw excel
    # if we should read it as lrw
    # so we trt to read it as lrw
    # if it's not, we read it as general
    # the other possibility when reading excels (that is not mentioned here) is to read it with ms markitdown
    # maybe it can be a better option in some cases
    try:
        data = read_excel_lrw.read_excel(inp_file)
        data_fetched = True
    except read_excel_lrw.MDMExcelReadFormatException:
        pass
    if not data_fetched:
        data = read_excel_general.read_excel(inp_file)

    result_json_fname = ( Path(inp_file).parents[0] / '{basename}{ext}'.format(basename=Path(inp_file).name,ext='.json') if Path(inp_file).is_file() else re.sub(r'^\s*?(.*?)\s*?$',lambda m: '{base}{added}'.format(base=m[1],added='.json'),'{path}'.format(path=inp_file)) )
    print('reading Excel: saving as "{fname}"'.format(fname=result_json_fname))
    outfile = open(result_json_fname, 'w')
    outfile.write(json.dumps(data, indent=4, default=json_dump_defaulthandler))

    time_finish = datetime.now()
    print('reading Excel: finished at {dt} (elapsed {duration})'.format(dt=time_finish,duration=time_finish-time_start))

if __name__ == '__main__':
    entry_point({'arglist_strict':True})
