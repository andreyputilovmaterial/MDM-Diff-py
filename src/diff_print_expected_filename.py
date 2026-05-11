import argparse
from pathlib import Path
# from random import choices
import re
import json
import sys # for error reporting, to print to stderr



if __name__ == '__main__':
    # run as a program
    from helper_make_diff_output_filename import make_output_fname
elif '.' in __name__:
    # package
    from .helper_make_diff_output_filename import make_output_fname
else:
    # included with no parent package
    from helper_make_diff_output_filename import make_output_fname






def entry_point(*argcs,**kwargs):

    # time_start = datetime.now()
    script_name = 'mdmtoolsap diff script'

    parser = argparse.ArgumentParser(
        description="Find Diff",
        prog='diffscript'
    )
    parser.add_argument(
        '-1',
        '--cmp-scheme-left',
        type=str,
        help='JSON with fields data from Input File A',
        required=True
    )
    parser.add_argument(
        '-2',
        '--cmp-scheme-right',
        type=str,
        help='JSON with fields data from Input File B',
        required=True
    )
    # parser.add_argument(
    #     '--cmp-format',
    #     help='Format: print results as 2 separate columns, or combine; possible values: sidebyside (default), sidebyside_distant, combined',
    #     type=str,
    #     required=False
    # )
    # parser.add_argument(
    #     '--config-skip-rows-nochange',
    #     help='Special flag to indicate that we should not add all rows to sections where nothing changed; I prefer to have this set to false in MDD - if nothing changed in shared lists we prefer to still see shared lists; but I prefer to have this set to true for Excel - having so many rows is unnecessary',
    #     action='store_true',
    #     required=False
    # )
    # parser.add_argument(
    #     '--config-do-not-show-content-rows-moved-from',
    #     help='Special flag to indicate that we should not print contents of "moved from" rows',
    #     action='store_true',
    #     required=False
    # )
    # # parser.add_argument(
    # #     '--config-use-hierarchical-name-structure',
    # #     help='Special flag to control if items names should be treated hierarhical',
    # #     action='store_true',
    # #     required=False
    # # )
    # parser.add_argument(
    #     '--config-casesensitive-item-list-comparison',
    #     help='Special flag to indicate if item name is a case-sensitive indentifier, or not and items written in different capitalization should be treated as same item',
    #     choices=('ignorecase','strict','auto',),
    #     default='auto',
    #     required=False
    # )
    # parser.add_argument(
    #     '--config-unordered-item-list-comparison',
    #     help='Special flag to indicate if different position of a row in input scheme is considered a change itself, without anything indicating a change in some column',
    #     choices=('ordered','unordered','auto',),
    #     default='auto',
    #     required=False
    # )
    # parser.add_argument(
    #     '--verbose-logging',
    #     help='Controls how detailed should it be printing progress details to console - set to level 0 (means, off), 1, 2, etc, or "auto" (that is the default, that turns to 0 or 1 based on detected complexity)',
    #     choices=('auto','0','1','2','3','4','5','6','7','8','9',),
    #     default='auto',
    #     required=False
    # )
    parser.add_argument(
        '--output-filename',
        help='Set preferred output file name, with path',
        type=str,
        required=False
    )
    parser.add_argument(
        '--output-filename-prefix', # TODO: probably needs to be cleaned, in ongoing efforts to housekeep - I think this is not really used
        help='Set additional prefix added to output file name (not working if --output-filename is set)',
        type=str,
        required=False
    )
    parser.add_argument(
        '--output-filename-suffix', # TODO: probably needs to be cleaned, in ongoing efforts to housekeep - I think this is not really used
        help='Set additional suffix added to output file name (not working if --output-filename is set)',
        type=str,
        required=False
    )
    # parser.add_argument(
    #     '--norun-special-onlyprintoutputfilename', # TODO: remove frmo here, add a separate file, called via --program something
    #     help='A special flag, the script does not run, does not read input files, does not cal;culate diff, does not write anything to files, does not print messages - it only print resulting output file name to console',
    #     action='store_true',
    #     required=False
    # )
    args, _ = parser.parse_known_args()
    
    inp_filename_left = ''
    if args.cmp_scheme_left:
        inp_filename_left = Path(args.cmp_scheme_left)
        inp_filename_left = f'{inp_filename_left.resolve()}'
    else:
        raise FileNotFoundError('Left CMP Source: file not provided; please use --cmp-scheme-left option')
    inp_filename_right = ''
    if args.cmp_scheme_right:
        inp_filename_right = Path(args.cmp_scheme_right)
        inp_filename_right = f'{inp_filename_right.resolve()}'
    else:
        raise FileNotFoundError('Right CMP Source: file not provided; please use --cmp-scheme-right option')

    report_part_filename_left = re.sub( r'\.json\s*?$', '', Path(inp_filename_left).name )
    report_part_filename_right = re.sub( r'\.json\s*?$', '', Path(inp_filename_right).name )
    result_final_fname = ''
    if args.output_filename:
        result_final_fname = Path(args.output_filename)
        if args.output_filename_prefix:
            raise FileNotFoundError('diff script: --output-filename-prefix: this option can\'t be set when --output-filename is provided')
        if args.output_filename_suffix:
            raise FileNotFoundError('diff script: --output-filename-suffix: this option can\'t be set when --output-filename is provided')
    else:
        def validate_fname_part(path):
            try:
                return f'{path}' == f'{Path(path).name}'
            except Exception:
                return False
        report_filename_prefixpart = 'report.diff.'
        report_filename_suffixpart = ''
        if args.output_filename_prefix:
            report_filename_prefixpart = args.output_filename_prefix
            if not validate_fname_part(report_filename_prefixpart):
                raise FileNotFoundError('diff script: output filename prefix: not valid name (please check the --output-filename-prefix option you are passing)')
        if args.output_filename_suffix:
            report_filename_suffixpart = args.output_filename_suffix
            if not validate_fname_part(report_filename_suffixpart):
                raise FileNotFoundError('diff script: output filename suffix: not valid name (please check the --output-filename-suffix option you are passing)')
        report_filename_filenamepart = make_output_fname(
            prefix = report_filename_prefixpart,
            filename_left = report_part_filename_left,
            filename_right = report_part_filename_right,
            suffix = report_filename_suffixpart,
            format = 'json',
        )
        report_filename_pathpart = Path(inp_filename_right).parents[0] # right!
        result_final_fname = report_filename_pathpart / report_filename_filenamepart
    
    print(result_final_fname)



if __name__ == '__main__':
    entry_point()
