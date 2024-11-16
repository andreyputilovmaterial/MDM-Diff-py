
import argparse

from pathlib import Path




if __name__ == '__main__':
    # run as a program
    import find_mdm_diff
    from lib.mdmreadpy import read_mdd
    from lib.otherformatsreadpy_txt import read as read_txt
    from lib.otherformatsreadpy_excel import read as read_excel
    from lib.mdmreadpy.lib.mdmreportpy import report_create
elif '.' in __name__:
    # package
    from . import find_mdm_diff
    from .lib.mdmreadpy import read_mdd
    from .lib.otherformatsreadpy_txt import read as read_txt
    from .lib.otherformatsreadpy_excel import read as read_excel
    from .lib.mdmreadpy.lib.mdmreportpy import report_create
else:
    # included with no parent package
    import find_mdm_diff
    from lib.mdmreadpy import read_mdd
    from lib.otherformatsreadpy_txt import read as read_txt
    from lib.otherformatsreadpy_excel import read as read_excel
    from lib.mdmreadpy.lib.mdmreportpy import report_create





# import json, re
from datetime import datetime, timezone



def call_diff_program():
    return find_mdm_diff.entry_point({'arglist_strict':False})

def call_read_mdd_program():
    return read_mdd.entry_point({'arglist_strict':False})

def call_read_excel_program():
    return read_excel.entry_point({'arglist_strict':False})

def call_read_txt_program():
    return read_txt.entry_point({'arglist_strict':False})

def call_report_program():
    return report_create.entry_point({'arglist_strict':False})






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
        elif args.program=='read_mdd':
            call_read_mdd_program()
        elif args.program=='read_txt':
            call_read_txt_program()
        elif args.program=='read_excel':
            call_read_excel_program()
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

