
import argparse
# from pathlib import Path
import traceback






if __name__ == '__main__':
    # run as a program
    import diff
    from lib.mdmreadpy import read_mdd
    from lib.otherformatsreadpy_txt import read as read_txt
    from lib.otherformatsreadpy_general_msmarkitdown import read as read_msmarkitdown
    from lib.otherformatsreadpy_excel import read_excel_entry as read_excel
    from lib.otherformatsreadpy_spss import read as read_spss
    from lib.mdmreadpy.lib.mdmreportpy import report_create
elif '.' in __name__:
    # package
    from . import diff
    from .lib.mdmreadpy import read_mdd
    from .lib.otherformatsreadpy_txt import read as read_txt
    from .lib.otherformatsreadpy_general_msmarkitdown import read as read_msmarkitdown
    from .lib.otherformatsreadpy_excel import read_excel_entry as read_excel
    from .lib.otherformatsreadpy_spss import read as read_spss
    from .lib.mdmreadpy.lib.mdmreportpy import report_create
else:
    # included with no parent package
    import diff
    from lib.mdmreadpy import read_mdd
    from lib.otherformatsreadpy_txt import read as read_txt
    from lib.otherformatsreadpy_general_msmarkitdown import read as read_msmarkitdown
    from lib.otherformatsreadpy_excel import read_excel_entry as read_excel
    from lib.otherformatsreadpy_spss import read as read_spss
    from lib.mdmreadpy.lib.mdmreportpy import report_create





# import json, re
from datetime import datetime, timezone



def call_diff_program():
    return diff.entry_point({'arglist_strict':False})

def call_read_mdd_program():
    return read_mdd.entry_point({'arglist_strict':False})

def call_read_excel_program():
    return read_excel.entry_point({'arglist_strict':False})

def call_read_spss_program():
    return read_spss.entry_point({'arglist_strict':False})

def call_read_txt_program():
    return read_txt.entry_point({'arglist_strict':False})

def call_read_msmarkitdown_program():
    return read_msmarkitdown.entry_point({'arglist_strict':False})

def call_report_program():
    return report_create.entry_point({'arglist_strict':False})

def call_test_program():
    print('hello, world!')
    return True




run_programs = {
    'diff': call_diff_program,
    'read_mdd': call_read_mdd_program,
    'read_txt': call_read_txt_program,
    'read_excel': call_read_excel_program,
    'read_spss': call_read_spss_program,
    'read_msmarkitdown': call_read_msmarkitdown_program,
    'report': call_report_program,
    'test': call_test_program,
}



def main():
    try:
        parser = argparse.ArgumentParser(
            description="Universal caller of mdmtoolsap-py utilities"
        )
        parser.add_argument(
            #'-1',
            '--program',
            choices=dict.keys(run_programs),
            type=str,
            required=True
        )
        args, args_rest = parser.parse_known_args()
        if args.program:
            program = '{arg}'.format(arg=args.program)
            if program in run_programs:
                run_programs[program]()
            else:
                raise AttributeError('program to run not recognized: {program}'.format(program=args.program))
        else:
            print('program to run not specified')
            raise AttributeError('program to run not specified')
    except Exception as e:
        # the program is designed to be user-friendly
        # that's why we reformat error messages a little bit
        # stack trace is still printed (I even made it longer to 20 steps!)
        # but the error message itself is separated and printed as the last message again

        # for example, I don't write "print('File Not Found!');exit(1);", I just write "raise FileNotFoundErro()"
        print('')
        print('Stack trace:')
        print('')
        traceback.print_exception(e,limit=20)
        print('')
        print('')
        print('')
        print('Error:')
        print('')
        print('{e}'.format(e=e))
        print('')
        exit(1)


if __name__ == '__main__':
    main()


