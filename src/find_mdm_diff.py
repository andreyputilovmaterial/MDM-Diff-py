import sys
from pathlib import Path
import re
inp_mdd_l = sys.argv[1]
inp_mdd_r = sys.argv[2]
report_part_mdd_left_filename = re.sub( r'\.mdd\.json', '.mdd', Path(inp_mdd_l).name )
report_part_mdd_right_filename = re.sub( r'\.mdd\.json', '.mdd', Path(inp_mdd_r).name )
report_filename = 'report.diff.{mdd_l}-{mdd_r}.json'.format(mdd_l=report_part_mdd_left_filename,mdd_r=report_part_mdd_right_filename)
result_json_fname = ( Path(inp_mdd_l).parents[0] / report_filename )
print(result_json_fname)