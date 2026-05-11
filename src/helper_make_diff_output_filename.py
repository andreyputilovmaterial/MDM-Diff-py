
from difflib import SequenceMatcher

if __name__ == '__main__':
    # run as a program
    from diff_engine import diff_functions
elif '.' in __name__:
    # package
    from .diff_engine import diff_functions
else:
    # included with no parent package
    from diff_engine import diff_functions




def make_diff_fname_part(filename_left,filename_right):
    def trim_list(lst):
        start = 0
        end = len(lst)
        while start < end and (lst[start] is None or lst[start] == ''):
            start += 1
        while end > start and (lst[end-1] is None or lst[end-1] == ''):
            end -= 1
        return lst[start:end]
    filename_left = f'{filename_left}'
    filename_right = f'{filename_right}'
    f_ar_left = diff_functions.text_split_words(filename_left)
    f_ar_right = diff_functions.text_split_words(filename_right)
    sm = SequenceMatcher(None,[s.lower() for s in f_ar_left],[s.lower() for s in f_ar_right])
    result = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        part = ''
        if tag=='equal':
            part = "".join(f_ar_left[i1:i2])
        elif tag == 'replace':
            part = f'{"".join(f_ar_left[i1:i2])}-{"".join(f_ar_right[j1:j2])}'
        elif tag == 'insert':
            part = "".join(f_ar_right[j1:j2])
        elif tag == 'delete':
            part = "".join(f_ar_left[i1:i2])
        else:
            raise Exception(f'Finding combined compiled output file name: Unrecognized piece from diff chunk {tag}')
        result.append(part)
    return '-'.join(trim_list(result))




def make_output_fname(prefix,filename_left,filename_right,suffix,format):
    ext = None
    if format == 'json':
        ext = 'json'
    elif format == 'html':
        ext = 'html'
    else:
        raise Exception(f'diff: make_output_fname: unknown ext: {ext}')
    return f'{prefix}{make_diff_fname_part(filename_left,filename_right)}{suffix}.{ext}'

