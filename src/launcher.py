
import argparse
# from pathlib import Path
import traceback, sys
import importlib






if __name__ == '__main__':
    # run as a program
    from GENERATED._VERSION import _VERSION as diff_script_version
    from diff_older import diff_obsolete
    import diff
    import diff_print_expected_filename
elif '.' in __name__:
    # package
    from .GENERATED._VERSION import _VERSION as diff_script_version
    from .diff_older import diff_obsolete
    from . import diff
    from . import diff_print_expected_filename
else:
    # included with no parent package
    from GENERATED._VERSION import _VERSION as diff_script_version
    from diff_older import diff_obsolete
    import diff
    import diff_print_expected_filename




# STDOUT_COLOR_RED = "\033[91m"
STDOUT_COLOR_RED = "\033[31m"
STDOUT_COLOR_RESET = "\033[0m"
STDOUT_COLOR_GREEN = "\033[32m"



def _import_module(flat_name):
    # Lazily import a reader/reporter module so the bundle can load without its
    # optional third-party dependencies (pandas, numpy, xlsxwriter, pydantic,
    # pywin32, markitdown, ...). `flat_name` is the module's dotted path below
    # the launcher package, e.g. 'lib.otherformatsreadpy_excel.read_excel_entry'.
    # Mirrors the three-way conditional import used by entry-point scripts.
    if __name__ == '__main__':
        # run as a program
        return importlib.import_module(flat_name)
    elif '.' in __name__:
        # package
        return importlib.import_module('.' + flat_name, package=__package__)
    else:
        # included with no parent package
        return importlib.import_module(flat_name)



def call_diff_obsolete_program(*argcs,**kwargs):
    return diff_obsolete.entry_point(*argcs,**kwargs)

def call_diff_program(*argcs,**kwargs):
    return diff.entry_point(*argcs,**kwargs)

def call_diff_filename_program(*argcs,**kwargs):
    return diff_print_expected_filename.entry_point(*argcs,**kwargs)

def call_read_mdd_program(*argcs,**kwargs):
    read_mdd = _import_module('lib.mdmreadpy.src.read_mdd')
    return read_mdd.entry_point(*argcs,**kwargs)

def call_build_schema_program(*argcs,**kwargs):
    mdd_to_schema = _import_module('lib.mddtoschema.src.read_mdd')
    return mdd_to_schema.entry_point(*argcs,**kwargs)

def call_read_excel_program(*argcs,**kwargs):
    read_excel = _import_module('lib.otherformatsreadpy_excel.read_excel_entry')
    return read_excel.entry_point(*argcs,**kwargs)

def call_read_spss_program(*argcs,**kwargs):
    read_spss = _import_module('lib.otherformatsreadpy_spss.read')
    return read_spss.entry_point(*argcs,**kwargs)

def call_read_txt_program(*argcs,**kwargs):
    read_txt = _import_module('lib.otherformatsreadpy_txt.read')
    return read_txt.entry_point(*argcs,**kwargs)

def call_read_msmarkitdown_program(*argcs,**kwargs):
    read_msmarkitdown = _import_module('lib.otherformatsreadpy_general_msmarkitdown.read')
    return read_msmarkitdown.entry_point(*argcs,**kwargs)

def call_report_html_program(*argcs,**kwargs):
    report_html_create = _import_module('lib.mdmreadpy.src.lib.mdmreportpy.src.report_create')
    return report_html_create.entry_point(*argcs,**kwargs)

def call_report_excel_program(*argcs,**kwargs):
    report_excel_create = _import_module('lib.mdmexcelreportpy.src.report_create')
    return report_excel_create.entry_point(*argcs,**kwargs)

def call_test_program(*argcs,**kwargs):
    msg = '''
hello, world! From diff
    '''
    print(msg)
    return True

def call_printversion_program(*argcs,**kwargs):
    msg = diff_script_version
    msg = msg.strip()
    print(msg)
    return True




run_programs = {
    'diff': call_diff_program,
    'diff_print_expected_filename': call_diff_filename_program,
    'diff_obsolete': call_diff_obsolete_program,
    'read_mdd': call_read_mdd_program,
    'mdd_to_schema': call_build_schema_program,
    'read_txt': call_read_txt_program,
    'read_excel': call_read_excel_program,
    'read_spss': call_read_spss_program,
    'read_msmarkitdown': call_read_msmarkitdown_program,
    'report': call_report_html_program,
    'report_html': call_report_html_program,
    'report_excel': call_report_excel_program,
    'test': call_test_program,
    'version': call_printversion_program,
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
                run_programs[program](args_rest)
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
        print('',file=sys.stderr)
        print('Stack trace:',file=sys.stderr)
        print('',file=sys.stderr)
        traceback.print_exception(e,limit=20)
        print('',file=sys.stderr)
        print('',file=sys.stderr)
        print('',file=sys.stderr)
        print(f'{STDOUT_COLOR_RED}Error:{STDOUT_COLOR_RESET}',file=sys.stderr)
        print('',file=sys.stderr)
        print(f'{STDOUT_COLOR_RED}{e}{STDOUT_COLOR_RESET}',file=sys.stderr)
        print('',file=sys.stderr)
        exit(1)


if __name__ == '__main__':
    main()
