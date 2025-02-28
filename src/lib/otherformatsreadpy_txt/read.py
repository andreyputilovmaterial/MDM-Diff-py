from pathlib import Path
import re
import argparse
import json
from datetime import datetime, timezone
import codecs




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





def detect_encoding(path, default='utf-8'):
    """Adapted from https://stackoverflow.com/questions/13590749/reading-unicode-file-data-with-bom-chars-in-python/24370596#24370596 """

    with open(path, 'rb') as f:
        raw = f.read(4)    # will read less if the file is smaller
    # BOM_UTF32_LE's start is equal to BOM_UTF16_LE so need to try the former first
    for enc, boms in \
            ('utf-8-sig', (codecs.BOM_UTF8,)), \
            ('utf-32', (codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)), \
            ('utf-16', (codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        for bom in boms:
            if raw.startswith(bom):
                # return enc, bom
                return enc
    # return default, None
    return default




def entry_point(config={}):
    time_start = datetime.now()
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
    inp_file = '{inp_file}'.format(inp_file=inp_file.resolve())
    if not(Path(inp_file).is_file()):
        raise FileNotFoundError('file not found: {fname}'.format(fname=inp_file))

    print('reading file: opening {fname}, script started at {dt}'.format(dt=time_start,fname=inp_file))

    textfilecontents = None

    encoding = detect_encoding(inp_file)
    
    with open(inp_file,'r',encoding=encoding) as inp_file_obj:
        textfilecontents = inp_file_obj.read()

    format_detect = None
    inp_file_namepart = '{f}'.format(f=Path(inp_file).name)
    if re.match(r'^\s*?TabScripts.*?\.mrs',inp_file_namepart,flags=re.I):
        format_detect = 'da_tablescrips'
    elif re.match(r'^\s*?PrepDataDMS.*?\.txt',inp_file_namepart,flags=re.I):
        format_detect = 'da_dms'

    read = None
    if format_detect=='da_tablescrips':
        read = reader_tablescripts.read
    else:
        read = reader_plain.read

    data = read(textfilecontents,{'filename':inp_file})

    result_json_fname = ( Path(inp_file).parents[0] / '{basename}{ext}'.format(basename=Path(inp_file).name,ext='.json') if Path(inp_file).is_file() else re.sub(r'^\s*?(.*?)\s*?$',lambda m: '{base}{added}'.format(base=m[1],added='.json'),'{path}'.format(path=inp_file)) )
    print('reading file: saving as "{fname}"'.format(fname=result_json_fname))
    outfile = open(result_json_fname, 'w')
    outfile.write(json.dumps(data, indent=4))

    time_finish = datetime.now()
    print('MDM read script: finished at {dt} (elapsed {duration})'.format(dt=time_finish,duration=time_finish-time_start))

if __name__ == '__main__':
    entry_point({'arglist_strict':True})
