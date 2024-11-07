
import argparse

from pathlib import Path




if __name__ == '__main__':
    # run as a program
    import find_mdm_diff
    from lib.mdmreadpy import read_mdd
    from lib.mdmreadpy.lib.mdmreportpy import report_create
elif '.' in __name__:
    # package
    from . import find_mdm_diff
    from .lib.mdmreadpy import read_mdd
    from .lib.mdmreadpy.lib.mdmreportpy import report_create
else:
    # included with no parent package
    import find_mdm_diff
    from lib.mdmreadpy import read_mdd
    from lib.mdmreadpy.lib.mdmreportpy import report_create





import json, re
from datetime import datetime, timezone



def call_diff_program():
    time_start = datetime.now()
    parser = argparse.ArgumentParser(
        description="Find Diff"
    )
    parser.add_argument(
        '-1',
        '--mdd_scheme_left',
        help='JSON with fields data from Input MDD A',
        required=True
    )
    parser.add_argument(
        '-2',
        '--mdd_scheme_right',
        help='JSON with fields data from Input MDD B',
        required=True
    )
    args, args_rest = parser.parse_known_args()
    inp_mdd_l = ''
    if args.mdd_scheme_left:
        inp_mdd_l = Path(args.mdd_scheme_left)
        inp_mdd_l = '{inp_mdd_l}'.format(inp_mdd_l=inp_mdd_l.resolve())
    else:
        raise FileNotFoundError('Left MDD: file not provided')
    inp_mdd_r = ''
    if args.mdd_scheme_right:
        inp_mdd_r = Path(args.mdd_scheme_right)
        inp_mdd_r = '{inp_mdd_l}'.format(inp_mdd_l=inp_mdd_r.resolve())
    else:
        raise FileNotFoundError('Right MDD: file not provided')
    # inp_file_specs = open(inp_file_specs_name, encoding="utf8")

    if not(Path(inp_mdd_l).is_file()):
        raise FileNotFoundError('file not found: {fname}'.format(fname=inp_mdd_l))
    if not(Path(inp_mdd_r).is_file()):
        raise FileNotFoundError('file not found: {fname}'.format(fname=inp_mdd_r))
    
    print('MDM diff script: script started at {dt}'.format(dt=time_start))

    result = find_mdm_diff.find_diff(inp_mdd_l,inp_mdd_r)
    
    result_json = json.dumps(result, indent=4)
    report_part_mdd_left_filename = re.sub( r'\.mdd\.json', '.mdd', Path(inp_mdd_l).name )
    report_part_mdd_right_filename = re.sub( r'\.mdd\.json', '.mdd', Path(inp_mdd_r).name )
    report_filename = 'report.diff.{mdd_l}-{mdd_r}.json'.format(mdd_l=report_part_mdd_left_filename,mdd_r=report_part_mdd_right_filename)
    result_json_fname = ( Path(inp_mdd_l).parents[0] / report_filename )
    print('MDM diff script: saving as "{fname}"'.format(fname=result_json_fname))
    with open(result_json_fname, "w") as outfile:
        outfile.write(result_json)

    time_finish = datetime.now()
    print('MDM diff script: finished at {dt} (elapsed {duration})'.format(dt=time_finish,duration=time_finish-time_start))





def call_mddread_program():
    time_start = datetime.now()
    parser = argparse.ArgumentParser(
        description="Read MDD"
    )
    parser.add_argument(
        '-1',
        '--mdd',
        help='Input MDD',
        required=True
    )
    parser.add_argument(
        '--method',
        default='open',
        help='Method',
        required=False
    )
    parser.add_argument(
        '--config-features',
        help='Config: list features (default is label,properties,translations)',
        required=False
    )
    parser.add_argument(
        '--config-contexts',
        help='Config: list contexts (default is Question,Analysis)',
        required=False
    )
    parser.add_argument(
        '--config-sections',
        help='Config: list sections (default is mdmproperties,languages,shared_lists,fields,pages,routing)',
        required=False
    )
    args, args_rest = parser.parse_known_args()
    inp_mdd = None
    if args.mdd:
        inp_mdd = Path(args.mdd)
        inp_mdd = '{inp_mdd}'.format(inp_mdd=inp_mdd.resolve())
    # inp_file_specs = open(inp_file_specs_name, encoding="utf8")

    method = '{arg}'.format(arg=args.method) if args.method else 'open'

    config = {
        # 'features': ['label','attributes','properties','translations'], # ,'scripting'],
        'features': ['label','attributes','properties','translations','scripting'],
        'sections': ['mdmproperties','languages','shared_lists','fields','pages','routing'],
        'contexts': ['Question','Analysis']
    }
    if args.config_features:
        config['features'] = args.config_features.split(',')
    if args.config_contexts:
        config['contexts'] = args.config_contexts.split(',')
    if args.config_sections:
        config['sections'] = args.config_sections.split(',')

    print('MDM read script: script started at {dt}'.format(dt=time_start))

    with read_mdd.MDMDocument(inp_mdd,method,config) as doc:

        result = doc.read()
        
        result_json = json.dumps(result, indent=4)
        result_json_fname = ( Path(inp_mdd).parents[0] / '{basename}{ext}'.format(basename=Path(inp_mdd).name,ext='.json') if Path(inp_mdd).is_file() else re.sub(r'^\s*?(.*?)\s*?$',lambda m: '{base}{added}'.format(base=m[1],added='.json'),'{path}'.format(path=inp_mdd)) )
        print('MDM read script: saving as "{fname}"'.format(fname=result_json_fname))
        with open(result_json_fname, "w") as outfile:
            outfile.write(result_json)

    time_finish = datetime.now()
    print('MDM read script: finished at {dt} (elapsed {duration})'.format(dt=time_finish,duration=time_finish-time_start))




def call_report_program():
    time_start = datetime.now()
    parser = argparse.ArgumentParser(
        description="Produce a summary of MDD in html (read from json)"
    )
    parser.add_argument(
        '--inpfile',
        help='JSON with Input MDD map'
    )
    args, args_rest = parser.parse_known_args()
    input_map_filename = None
    if args.inpfile:
        input_map_filename = Path(args.inpfile)
        input_map_filename = '{input_map_filename}'.format(input_map_filename=input_map_filename.resolve())
    # input_map_filename_specs = open(input_map_filename_specs_name, encoding="utf8")

    print('MDM report script: script started at {dt}'.format(dt=time_start))

    mdd_map_in_json = None
    with open(input_map_filename, encoding="utf8") as input_map_file:
        mdd_map_in_json = json.load(input_map_file)

    result = report_create.produce_html(mdd_map_in_json)
    
    result_fname = ( Path(input_map_filename).parents[0] / '{basename}{ext}'.format(basename=Path(input_map_filename).name,ext='.html') if Path(input_map_filename).is_file() else re.sub(r'^\s*?(.*?)\s*?$',lambda m: '{base}{added}'.format(base=m[1],added='.html'),'{path}'.format(path=input_map_filename)) )
    print('MDM report script: saving as "{fname}"'.format(fname=result_fname))
    with open(result_fname, "w") as outfile:
        outfile.write(result)

    time_finish = datetime.now()
    print('MDM report script: finished at {dt} (elapsed {duration})'.format(dt=time_finish,duration=time_finish-time_start))






def main():
    parser = argparse.ArgumentParser(
        description="Universal caller of mdm-py utilities"
    )
    parser.add_argument(
        '-1',
        '--program',
        required=True
    )
    args, args_rest = parser.parse_known_args()
    if args.program:
        if args.program=='diff':
            call_diff_program()
        elif args.program=='read':
            call_mddread_program()
        elif args.program=='report':
            call_report_program()
        elif args.program=='test':
            print('test!')
        else:
            print('program to run not recognized: {program}'.format(program=args.program))
            raise AttributeError('program to run not recognized: {program}'.format(program=args.program))
    else:
        print('program to run not specified')
        raise AttributeError('program to run not specified')


if __name__ == '__main__':
    main()

