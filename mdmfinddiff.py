
import sys, os
import json, re
from datetime import datetime

from collections import namedtuple










def escape_html(s):
    return re.sub(r'[^\w]',lambda char: '&#{num};'.format(num=ord(char[0][0])),s)

def unescape_html(s):
    return re.sub(r'&\#(\d+);',lambda m: '{result}'.format(result=chr(int(m[1]))),s)



def split_words(s):
    return '{s}{eend}'.format(s=re.sub(r'(?:(?:&#60|<)(?:&#60|<)HIDDENLINEBREAK(?:&#62;|>)(?:&#62;|>)|(?:(?:\b\w+\b)|(?:\s+)|.))',lambda m: '<<MDMREPDELIMITER>>{m}'.format(m=m[0]),s),eend='<<MDMREPDELIMITER>>').split('<<MDMREPDELIMITER>>')


def is_info_item(item_name):
    return re.match(r'^\s*?Info&#58;&#32;',item_name)


def recognize_col_type_by_label(col_def):
    col_type = None
    if re.match(r'^(?:\s|(?:&#32;))*?Label(?:\s|(?:&#32;))*?(?:(?:\(|(?:&#40;)).*?(?:\)|(?:&#41;)))?(?:\s|(?:&#32;))*?$',col_def):
        # Label
        col_type = 'label'
    elif  re.match(r'^(?:\s|(?:&#32;))*?(?:Custom)?(?:\s|(?:&#32;))*?(?:Property|properties)(?:\s|(?:&#32;))*?(?:(?:\(|(?:&#40;)).*?(?:\)|(?:&#41;)))?(?:\s|(?:&#32;))*?$',col_def):
        # Custom properties
        col_type = 'properties'
    elif  re.match(r'^(?:\s|(?:&#32;))*?Translate(?:\s|(?:&#32;))*?(?:(?:\(|(?:&#40;))(?:\s|(?:&#32;))*?\w+(?:\s|(?:&#32;))*?(?:\)|(?:&#41;)))(?:\s|(?:&#32;))*?$',col_def):
        # Translations
        col_type = 'translations'
    else:
        col_type = True
    return col_type

def unicode_remove_accents(txt):
    raise Exception('remove accents func: not implemented; please grab some implementation suitable for your needs')









DiffItemKeep = namedtuple('DiffItemKeep', ['line'])
DiffItemInsert = namedtuple('DiffItemInsert', ['line'])
DiffItemRemove = namedtuple('DiffItemRemove', ['line'])



# a function or Myers diff
# re-written to python from js by AP 11/30/2022
# sourced 11/17/2022 from https://github.com/wickedest/myers-diff, Apache 2.0 license */ /* authors can be found there on that page */ /* license is not attached but can be found here https:/* github.com/wickedest/myers-diff/blob/master/LICENSE */

class MyersDiffSplitter:
    def __init__(self,data,delimiter):
        self.data = data
        self.pos = None
        self.start = None
        self.delimiter = delimiter
    def __iter__(self):
        self.start = 0
        self.pos = ( 0 if not self.delimiter else ( data.index(self.delimiter, self.start) if self.delimiter in self.data[self.start:] else -1 ) )
        return self
    def __next__(self):
        if len(self.data) == 0:
            raise StopIteration
        elif not self.delimiter:
            if self.start>=len(self.data):
                raise StopIteration
            else:
                part = {'text':self.data[self.start],'pos':self.start}
                self.start = self.start + 1
                return part
        elif self.pos<0:
            if self.start<=len(self.data):
                # handle remaining text.  the `start` might be at some */ /*  position less than `text.length`.  it may also be _exactly_ */ /*  `text.length` if the `text` ends with a double `ch`, e.g. */ /*  "\n\n", the `start` is set to `pos + 1` below, which is one */ /*  after the first "\n" of the pair.  it would also be split. */
                part = {'text':self.data[self.start:],'pos':self.start}
                self.pos = -1
                self.start = len(self.data) + 1
                return part
            else:
                raise StopIteration
        else:
            word = self.data[self.start:self.pos]
            part = {'text':word,'pos':self.start}
            self.start = self.pos + 1
            self.pos = ( 0 if not self.delimiter else ( data.index(self.delimiter, self.start) if self.delimiter in self.data[self.start:] else -1 ) )
            return part

def myers_diff_get_default_settings():
    return {
        'compare': 'array', # array|lines|words|chars
        'ignorewhitespace': False,
        'ignorecase': False,
        'ignoreaccents': False
    }

class MyersDiffEncodeContext:
    def __init__(self, encoder, data, options={}):
        re = None
        self.encoder = encoder
        self._codes = {}
        self._modified = {}
        self._parts = [];
        count = 0
        splitter_delimiter = None
        if 'compare' in options:
            if options['compare']=='lines':
                splitter_delimiter = "\n"
            elif options['compare']=='words':
                splitter_delimiter = ' '
            elif options['compare']=='chars':
                splitter_delimiter = ''
            elif options['compare']=='array':
                splitter_delimiter = None
            else:
                # default
                # that would be chars, or array, that would work the same
                splitter_delimiter = None
        split = MyersDiffSplitter(data,splitter_delimiter)
        part = None
        for part in split:
            # if options.lowercase..., options.ignoreAccents
            # line = lower(line) ...
            # part = { 'text': part_txt, 'pos': count }
            line = str(part['text'])
            if ('ignorewhitespace' in options) and (options['ignorewhitespace']):
                line = re.sub(r'^\s*','',re.sub(r'\s*$','',re.sub(r'\s+',' ',line)))
            if ('ignorecase' in options) and (options['ignorecase']):
                line = line.lower()
            if ('ignoreaccents' in options) and (options['ignoreaccents']):
                line = unicode_remove_accents(line)
            aCode = encoder.get_code(line)
            self._codes[str(count)] = aCode
            self._parts.append(part)
            count = count + 1
    def finish(self):
        del self.encoder
    def _get_codes(self):
        return self._codes
    def _get_length(self):
        return len(self._codes.keys())
    def _get_modified(self):
        return self._modified
    codes = property(_get_codes)
    modified = property(_get_modified)
    length = property(_get_length)

class MyersDiffEncoder:
    code = 0
    diff_codes = {}
    def __init__(self):
        self.code = 0
        self.diff_codes = {}
    def encode(self, data,options={}):
        return MyersDiffEncodeContext(self,data,options)
    def get_code(self, line):
        if str(line) in self.diff_codes:
            return self.diff_codes[str(line)]
        self.code = self.code + 1
        self.diff_codes[str(line)] = self.code
        return self.code

class Myers:
    @staticmethod
    def compare_lcs(lhsctx, rhsctx, callback):
        lhs_start = 0
        rhs_start = 0
        lhs_line = 0
        rhs_line = 0
        while ((lhs_line < lhsctx.length) or (rhs_line < rhsctx.length)):
            if not str(lhs_line) in lhsctx.modified:
                lhsctx.modified[str(lhs_line)] = False
            if not str(rhs_line) in rhsctx.modified:
                rhsctx.modified[str(rhs_line)] = False
            if ((lhs_line < lhsctx.length) and (not lhsctx.modified[str(lhs_line)]) and (rhs_line < rhsctx.length) and (not rhsctx.modified[str(rhs_line)])):
                # equal lines
                lhs_line = lhs_line + 1
                rhs_line = rhs_line + 1
            else:
                # maybe deleted and/or inserted lines
                lhs_start = lhs_line
                rhs_start = rhs_line
                while ((lhs_line < lhsctx.length) and ((rhs_line >= rhsctx.length) or ((str(lhs_line) in lhsctx.modified) and (lhsctx.modified[str(lhs_line)])))):
                    lhs_line = lhs_line + 1
                while ((rhs_line < rhsctx.length) and ((lhs_line >= lhsctx.length) or ((str(rhs_line) in rhsctx.modified) and (rhsctx.modified[str(rhs_line)])))):
                    rhs_line = rhs_line + 1
                if ((lhs_start < lhs_line) or (rhs_start < rhs_line)):
                    lat = min([lhs_start, lhsctx.length-1 if lhsctx.length>0 else 0])
                    rat = min([rhs_start, rhsctx.length-1 if rhsctx.length>0 else 0])
                    lpart = lhsctx._parts[min([lhs_start, lhsctx.length - 1])]
                    rpart = rhsctx._parts[min([rhs_start, rhsctx.length - 1])]
                    item = {
                        'lhs': {
                            'at': lat,
                            'del': lhs_line - lhs_start,
                            'pos': lpart['pos'] if lpart else None,
                            'text': lpart['text'] if lpart else None
                        },
                        'rhs': {
                            'at': rat,
                            'add': rhs_line - rhs_start,
                            'pos': rpart['pos'] if rpart else None,
                            'text': rpart['text'] if rpart else None
                        }
                    }
                    callback(item)

    @staticmethod
    def get_shortest_middle_snake(lhsctx, lhs_lower, lhs_upper, rhsctx, rhs_lower, rhs_upper, vectorU, vectorD):
        max = lhsctx.length + rhsctx.length + 1
        if not max:
            raise Exception('unexpected state');
        kdown = lhs_lower - rhs_lower
        kup = lhs_upper - rhs_upper
        delta = (lhs_upper - lhs_lower) - (rhs_upper - rhs_lower)
        odd = (delta & 1) != 0
        offset_down = max - kdown
        offset_up = max - kup
        maxd = ((lhs_upper - lhs_lower + rhs_upper - rhs_lower) // 2) + 1
        ret = {
            'x': 0,
            'y': 0
        }
        d = None
        k = None
        x = None
        y = None
        if offset_down + kdown + 1>=len(vectorD):
            # redim
            # print('redim {var} to {n}, len is {l}!'.format(var='vectorD',n=offset_down + kdown + 1,l=len(vectorD)))
            raise Exception('redim {var} to {n}, len is {l}!'.format(var='vectorD',n=offset_down + kdown + 1,l=len(vectorD)))
            # vectorD = [*vectorD,*[None for i in range(len(vectorD),offset_down + kdown + 1+1)]]
        vectorD[offset_down + kdown + 1] = lhs_lower
        if offset_up + kup - 1>=len(vectorU):
            # redim
            # print('redim {var} to {n}, len is {l}!'.format(var='vectorU',n=offset_up + kup - 1,l=len(vectorU)))
            raise Exception('redim {var} to {n}, len is {l}!'.format(var='vectorU',n=offset_up + kup - 1,l=len(vectorU)))
            # vectorU = [*vectorU,*[None for i in range(len(vectorU),offset_up + kup - 1+1)]]
        vectorU[offset_up + kup - 1] = lhs_upper
        for d in range(maxd+1):
            for k in range(kdown - d, kdown + d+1, 2):
                if (k == kdown - d):
                    x = vectorD[offset_down + k + 1]
                    # down
                else:
                    x = vectorD[offset_down + k - 1] + 1
                    # right
                    if ((k < (kdown + d)) and (vectorD[offset_down + k + 1] >= x)):
                        x = vectorD[offset_down + k + 1]
                        # down
                y = x - k
                # find the end of the furthest reaching forward D-path in diagonal k.
                while ((x < lhs_upper) and (y < rhs_upper) and (lhsctx.codes[str(x)] == rhsctx.codes[str(y)])):
                    x = x + 1
                    y = y + 1
                if offset_down + k>=len(vectorD):
                    # redim
                    # print('redim {var} to {n}, len is {l}!'.format(var='vectorD',n= offset_down + k,l=len(vectorD)))
                    raise Exception('redim {var} to {n}, len is {l}!'.format(var='vectorD',n= offset_down + k,l=len(vectorD)))
                    # vectorD = [*vectorD,*[None for i in range(len(vectorD),offset_down + k+1)]]
                vectorD[offset_down + k] = x
                # overlap ?
                if (odd and (kup - d < k) and (k < kup + d)):
                    if (vectorU[offset_up + k] <= vectorD[offset_down + k]):
                        ret['x'] = vectorD[offset_down + k]
                        ret['y'] = vectorD[offset_down + k] - k
                        return (ret)
            # Extend the reverse path.
            for k in range(kup - d, kup + d+1, 2):
                # find the only or better starting point
                if (k == kup + d):
                    x = vectorU[offset_up + k - 1]
                    # up
                else:
                    x = vectorU[offset_up + k + 1] - 1
                    # left
                    if ((k > kup - d) and (vectorU[offset_up + k - 1] < x)):
                        x = vectorU[offset_up + k - 1]
                        # up
                y = x - k
                while ((x > lhs_lower) and (y > rhs_lower) and (lhsctx.codes[str(x - 1)] == rhsctx.codes[str(y - 1)])):
                    # diagonal
                    x = x - 1
                    y = y - 1
                if offset_up + k>=len(vectorU):
                    # redim
                    # print('redim {var} to {n}, len is {l}!'.format(var='vectorU',n= offset_up + k,l=len(vectorU)))
                    raise Exception('redim {var} to {n}, len is {l}!'.format(var='vectorU',n= offset_up + k,l=len(vectorU)))
                    # vectorU = [*vectorU,*[None for i in range(len(vectorU),offset_up + k+1)]]
                vectorU[offset_up + k] = x
                # overlap ?
                if (not odd and (kdown - d <= k) and (k <= kdown + d)):
                    if offset_up + k>=len(vectorU):
                        # redim
                        # print('redim {var} to {n}, len is {l}!'.format(var='vectorU',n=offset_up + k,l=len(vectorU)))
                        raise Exception('redim {var} to {n}, len is {l}!'.format(var='vectorU',n=offset_up + k,l=len(vectorU)))
                        # vectorU = [*vectorU,*[None for i in range(len(vectorU),offset_up + k+1)]]
                    if offset_down + k>=len(vectorD):
                        # redim
                        # print('redim {var} to {n}, len is {l}!'.format(var='vectorD',n=offset_down + k,l=len(vectorD)))
                        raise Exception('redim {var} to {n}, len is {l}!'.format(var='vectorD',n=offset_down + k,l=len(vectorD)))
                        # vectorD = [*vectorD,*[None for i in range(len(vectorD),offset_down + k+1)]]
                    if (vectorU[offset_up + k] <= vectorD[offset_down + k]):
                        ret['x'] = vectorD[offset_down + k]
                        ret['y'] = vectorD[offset_down + k] - k
                        return (ret)
        # should never get to this state
        raise Exception('unexpected state')
    @staticmethod
    def get_longest_common_subsequence(lhsctx, lhs_lower, lhs_upper, rhsctx, rhs_lower, rhs_upper, vectorU, vectorD):
        # trim off the matching items at the beginning
        while ((lhs_lower < lhs_upper) and (rhs_lower < rhs_upper) and (lhsctx.codes[str(lhs_lower)] == rhsctx.codes[str(rhs_lower)])):
            lhs_lower = lhs_lower + 1
            rhs_lower = rhs_lower + 1
        # trim off the matching items at the end
        while ((lhs_lower < lhs_upper) and (rhs_lower < rhs_upper) and (lhsctx.codes[str(lhs_upper - 1)] == rhsctx.codes[str(rhs_upper - 1)])):
            lhs_upper = lhs_upper - 1
            rhs_upper = rhs_upper - 1
        if (lhs_lower == lhs_upper):
            while (rhs_lower < rhs_upper):
                rhsctx.modified[str(rhs_lower)] = True
                rhs_lower = rhs_lower + 1
        elif (rhs_lower == rhs_upper):
            while (lhs_lower < lhs_upper):
                lhsctx.modified[str(lhs_lower)] = True
                lhs_lower = lhs_lower + 1
        else:
            p_p = Myers.get_shortest_middle_snake(lhsctx, lhs_lower, lhs_upper, rhsctx, rhs_lower, rhs_upper, vectorU, vectorD)
            x = p_p['x']
            y = p_p['y']
            Myers.get_longest_common_subsequence(lhsctx, lhs_lower, x, rhsctx, rhs_lower, y, vectorU, vectorD)
            Myers.get_longest_common_subsequence(lhsctx, x, lhs_upper, rhsctx, y, rhs_upper, vectorU, vectorD)

    # Compare {@code lhs} to {@code rhs}.  Changes are compared from left
    # * to right such that items are deleted from left, or added to right,
    # * or just otherwise changed between them.
    # *
    # * @param   {string} lhs - The left-hand source text.
    # * @param   {string} rhs - The right-hand source text.
    @staticmethod
    def diff(lhs, rhs, options=None):
        encoder = MyersDiffEncoder()
        if (not hasattr(lhs,'__len__')):
            raise Exception('illegal argument \'lhs\'')
        if (not hasattr(rhs,'__len__')):
            raise Exception('illegal argument \'rhs\'')
        if not hasattr(options,'__getitem__'):
            options = {}
        settings = {**myers_diff_get_default_settings(),**options}
        lhsctx = encoder.encode(lhs,settings)
        rhsctx = encoder.encode(rhs,settings)
        # Myers.LCS(lhsctx, rhsctx)
        Myers.get_longest_common_subsequence(lhsctx, 0, lhsctx.length, rhsctx, 0, rhsctx.length, [None for i in range(0,4*(len(lhs)+len(rhs))+10)], [None for i in range(0,4*(len(lhs)+len(rhs))+10)] )
        # compare lhs/rhs codes and build a list of comparisons
        changes = []
        compare = 1 # that means lines not chars
        def _changeItem(item):
            # add context information
            def _lhs_get_part(n):
                return lhsctx._parts[n]
            def _rhs_get_part(n):
                return rhsctx._parts[n]
            item['lhs']['get_part'] = _lhs_get_part
            item['rhs']['get_part'] = _rhs_get_part
            if (compare == 0):
                # chars
                item['lhs']['length'] = item['lhs']['del']
                item['rhs']['length'] = item['rhs']['add']
            else:
                # words and lines
                item['lhs']['length'] = 0
                if (item['lhs']['del']):
                    # get the index of the second-last item being deleted
                    # plus its length, minus the start pos.
                    i = item['lhs']['at'] + item['lhs']['del'] - 1
                    part = lhsctx._parts[i]
                    item['lhs']['length'] = part['pos'] + 1 - lhsctx._parts[item['lhs']['at']]['pos']
                item['rhs']['length'] = 0
                if (item['rhs']['add']):
                    # get the index of the second-last item being added,
                    # plus its length, minus the start pos.
                    i = item['rhs']['at'] + item['rhs']['add'] - 1
                    part = rhsctx._parts[i]
                    item['rhs']['length'] = part['pos'] + 1 - rhsctx._parts[item['rhs']['at']]['pos']
            changes.append(item)
        Myers.compare_lcs(lhsctx, rhsctx, _changeItem)
        lhsctx.finish()
        rhsctx.finish()
        return changes

    # converts results formatted with lhs and rhs to a list with DiffItemKeep, DiffItemInsert, DiffItemRemove items
    @staticmethod
    def to_records(diff,a,b):
        results = []
        lastIndex = 0
        for diffObj in diff:
            results = [
                *results,
                *map(
                    lambda line: DiffItemKeep(line),
                    a[ lastIndex : diffObj['lhs']['at'] ]
                ),
                *map(
                    lambda line: DiffItemRemove(line),
                    a[ diffObj['lhs']['at'] : diffObj['lhs']['at'] + diffObj['lhs']['del'] ]
                ),
                *map(
                    lambda line: DiffItemInsert(line),
                    b[diffObj['rhs']['at'] : diffObj['rhs']['at'] + diffObj['rhs']['add'] ]
                )
            ]
            lastIndex = diffObj['lhs']['at'] + diffObj['lhs']['del']
        results = [
            *results,
            *map(
                lambda line: DiffItemKeep(line),
                a[lastIndex:]
            )
        ];
        return results









# the function to create data for the final report, and return it in json
def find_diff_jsonstr(json_lmdd,json_rmdd):

    time_start = datetime.utcnow()

    # this "data" contains also general fields for mdd names, timestamp, script ver, etc
    # here we go and iti it
    result = {
        "ReportType": "MDDDiff",
        "MDMREPSCRIPT": "true",
        "MDD_LEFT": json_lmdd['MDD'],
        "MDD_RIGHT": json_rmdd['MDD'],
        "DateTimeReportGenerated": str(datetime.utcnow()),
        "MDMREP_SCRIPT_VER": "latest",
        "FileProperties": {
            "ReportTitle": "MDM&#32;Diff&#32;{mdd_lmdd}&#32;vs&#32;{mdd_rmdd}".format(mdd_lmdd=json_lmdd['MDD'],mdd_rmdd=json_rmdd['MDD']),
            "ReportHeading": "MDM&#32;Diff&#32;{mdd_lmdd}&#32;vs&#32;{mdd_rmdd}".format(mdd_lmdd=json_lmdd['MDD'],mdd_rmdd=json_rmdd['MDD']),
            "ReportInfo": [
                escape_html('Hi! Please see the diff below.'),
                '{part1}{part2}{part3}{part4}{part5}'.format(part1=escape_html('Left MDD: '),part2=json_lmdd['MDD'],part3=escape_html(', right MDD: '),part4=json_rmdd['MDD'],part5=''),
                "Run&#58;&#32;{t}".format(t=escape_html(str(datetime.utcnow())))
            ]
        }
    }

    # here we check what columns are in input data files and create a combined column set that will be used in report
    columns_headers_lmdd = [ '{s}'.format(s=str(s)) for s in (json_lmdd['ColumnHeaders'] if 'ColumnHeaders'in json_lmdd else [''])[0:] ]
    columns_headers_rmdd = [ '{s}'.format(s=str(s)) for s in (json_rmdd['ColumnHeaders'] if 'ColumnHeaders'in json_rmdd else [''])[0:] ]
    columns_headers_check = []
    # combine left and right exclusing duplicates
    for col in columns_headers_lmdd[1:]:
        columns_headers_check.append(col)
    for col in columns_headers_rmdd[1:]:
        if not (col in columns_headers_check):
            columns_headers_check.append(col)
    # filter out some column types, i.e. translations if they do not exist in both files
    cols_temp_exclude = []
    for col in columns_headers_check:
        col_type = recognize_col_type_by_label(col)
        if col_type=='label':
            pass
        elif col_type=='properties':
            pass
        elif col_type=='translations':
            # it should exist in both MDDs, left and right, otherwise exclude
            if ( col in columns_headers_lmdd[1:] ) and ( col in columns_headers_rmdd[1:] ):
                # good to go, it exists in both files
                pass
            else:
                # exclude
                cols_temp_exclude.append(col)
        else:
            pass
    for col in cols_temp_exclude:
        columns_headers_check.remove(col)
    result['ColumnHeaders'] = [*['Diff&#32;flag','Item&#32;name&#44;&#32;or&#32;path'],*['&#40;Left&#32;MDD&#41;&#32;{col}'.format(col=col) for col in columns_headers_check],*['&#40;Right&#32;MDD&#41;&#32;{col}'.format(col=col) for col in columns_headers_check]]

    # "records" is the list of records in left and right input files
    records_lmdd = (json_lmdd['Records'] if 'Records' in json_lmdd else [])
    records_rmdd = (json_rmdd['Records'] if 'Records' in json_rmdd else [])
    # and "rows" are the same as records but not the whole row with cells for labels, properties, translations but just the first cell that is a question or category name, i.e. item name
    rows_lmdd = [ row[0] for row in records_lmdd ]
    rows_rmdd = [ row[0] for row in records_rmdd ]
    #rows_joined_lmdd = '\n'.join( rows_lmdd ) # no need to join in a string, we need an array
    #rows_joined_rmdd = '\n'.join( rows_rmdd )

    # and "records" is the variable for total records that we return in the report
    records = []

    # # temporary - save compared parts to files
    # report_file_name = 'a_test.json'
    # print("Writing results...\n")
    # with open(report_file_name,'w') as output_file:
    #     output_file.write(json.dumps(rows_lmdd))
    # report_file_name = 'b_test.json'
    # print("Writing results...\n")
    # with open(report_file_name,'w') as output_file:
    #     output_file.write(json.dumps(rows_rmdd))

    # go!
    # calculate diff
    print('Finding diff, which items were added or removed. The report for left MDD contains {len_lmdd}, the report for the right MDD contains {len_rmdd}. Working on diff...\n'.format(len_lmdd=len(rows_lmdd),len_rmdd=len(rows_rmdd)))
    # row_groups = [] # split by info items
    # last_group = []

    diff_total = Myers.diff(rows_lmdd, rows_rmdd,{'compare':'array','ignorecase':True})

    #
    # TODO: update to newer diff fn: done!
    diff_records = Myers.to_records(diff_total,rows_lmdd,rows_rmdd)
    print('Done. Finding diffs on labels in each row. In the report it would be {n123} rows. Working...\n'.format(n123=len(diff_records)))

    # create rows to be reported
    # the first cell is an indication (added, removed, anything else...)
    # the second cell is a question name (or item name, category name, etc...)
    # then go columns from input mdds labelled left and right
    # an example would be "diff -> Gender.Categories[Male] -> Male -> <b>Male</b>", a row of 4 cells

    # helper variables to control if runtime is too big and we need to print something to console so that the user knows about the progress
    time_last_reported = datetime.utcnow()
    counter_last_reported = 0
    counter = 0
    counter_total = len(diff_records)
    for elem in diff_records:
        # iterate over each line in the report
        # it is: kept, or deleted, or added

        # check if we need to update the user that it is running, if it takes too long
        if counter-counter_last_reported>100: # not every row, at least every 100-th, and then we check if time elapsed from the last update is more then 60 seconds
            time_now = datetime.utcnow()
            if (time_now - time_last_reported).total_seconds()>60:
                print('Checking for diffs in labels, processing line {nline} / {nlinetotal} ({per}%)\n'.format(nline=counter,nlinetotal=counter_total,per=round(counter*100/counter_total,1)))
                counter_last_reported = counter
                time_last_reported = time_now
        counter = counter + 1

        item_name = elem.line

        # self describing
        exists_lmdd = elem.line in rows_lmdd
        exists_rmdd = elem.line in rows_rmdd

        diff_flag = None
        # that incication, if it was added, removed, or whatever
        if isinstance(elem, DiffItemKeep):
            if is_info_item(item_name):
                diff_flag = '(info)'
            else:
                diff_flag = '???'
        elif isinstance(elem, DiffItemInsert):
            if exists_lmdd:
                diff_flag = '???'
            else:
                diff_flag = 'added'
        elif isinstance(elem, DiffItemRemove):
            if exists_rmdd:
                diff_flag = '(moved)'
            else:
                diff_flag = 'removed'
        else:
            raise Exception('unknown diff flag')

        # grab corresponding data from left MDD for the "elem.line" row
        reportline_row_lmdd = []
        for col_def in columns_headers_check:
            value = None
            if exists_lmdd:
                try:
                    index_row = rows_lmdd.index(elem.line)
                    index = columns_headers_lmdd.index(col_def)
                    value = records_lmdd[index_row][index] if index<len(records_lmdd[index_row]) else ''
                except ValueError:
                    value = ''
            else:
                value = ''
            reportline_row_lmdd.append(value)
        # and now from the right MDD
        reportline_row_rmdd = []
        for col_def in columns_headers_check:
            value = None
            if exists_rmdd:
                try:
                    index_row = rows_rmdd.index(elem.line)
                    index = columns_headers_rmdd.index(col_def)
                    value = records_rmdd[index_row][index] if index<len(records_rmdd[index_row]) else ''
                except ValueError:
                    value = ''
            else:
                value = ''
            reportline_row_rmdd.append(value)

        # diff!
        # check for differences in each field - in labels, properties, etc
        if not (diff_flag in ['added','removed']):
            # we skip rows where the row was added or removed - it definitely changed, as one side simply does not exist; no need to compare
            did_any_col_change = False
            did_any_significant_col_change = False
            for col_num in range(len(columns_headers_check)):
                col_def = columns_headers_check[col_num]
                cell_contents_lmdd = reportline_row_lmdd[col_num]
                cell_contents_rmdd = reportline_row_rmdd[col_num]
                if diff_flag=='(moved)':
                    # blind up contents - it will appear at a different line, where it's moved
                    cell_contents_lmdd = ''
                    cell_contents_rmdd = ''
                is_col_significant = True # we can disregard differences in custom properties or translations
                col_type = recognize_col_type_by_label(col_def)
                if col_type == 'label':
                    # Label = significant
                    is_col_significant = True
                elif col_type == 'properties':
                    # Custom properties = not significant
                    is_col_significant = False
                elif col_type == 'translations':
                    # Translations = not significant
                    is_col_significant = False
                else:
                    is_col_significant = True

                did_col_change = False
                did_significant_col_change = False

                if ( (type(cell_contents_lmdd) is str) and (type(cell_contents_rmdd) is str) ):
                    cell_contents_splitwords_lmdd = None
                    cell_contents_splitwords_rmdd = None
                    if cell_contents_lmdd==cell_contents_rmdd:
                        # no need to check full, if matches
                        diff_col = []
                        # cell_contents_upd_lmdd = cell_contents_lmdd
                        # cell_contents_upd_rmdd = cell_contents_rmdd
                        cell_contents_splitwords_lmdd = [unescape_html(cell_contents_lmdd)]
                        cell_contents_splitwords_rmdd = [unescape_html(cell_contents_rmdd)]
                        cell_contents_upd_lmdd = ''
                        cell_contents_upd_rmdd = ''
                        # continue
                    else:
                        cell_contents_splitwords_lmdd = split_words(unescape_html(cell_contents_lmdd))
                        cell_contents_splitwords_rmdd = split_words(unescape_html(cell_contents_rmdd))
                        diff_col = Myers.diff(cell_contents_splitwords_lmdd,cell_contents_splitwords_rmdd,{'compare':'array'})
                        cell_contents_upd_lmdd = ''
                        cell_contents_upd_rmdd = ''
                    # TODO: update to newer diff fn
                    diff_col_records = Myers.to_records(diff_col,cell_contents_splitwords_lmdd,cell_contents_splitwords_rmdd)
                    # combine parts
                    for i in range(len(diff_col_records)):
                        if i>0:
                            if isinstance(diff_col_records[i],DiffItemKeep) and isinstance(diff_col_records[i-1],DiffItemKeep):
                                diff_col_records[i] = DiffItemKeep(diff_col_records[i-1].line+diff_col_records[i].line)
                                diff_col_records[i-1] = DiffItemKeep('')
                            if isinstance(diff_col_records[i],DiffItemInsert) and isinstance(diff_col_records[i-1],DiffItemInsert):
                                diff_col_records[i] = DiffItemInsert(diff_col_records[i-1].line+diff_col_records[i].line)
                                diff_col_records[i-1] = DiffItemKeep('')
                            if isinstance(diff_col_records[i],DiffItemRemove) and isinstance(diff_col_records[i-1],DiffItemRemove):
                                diff_col_records[i] = DiffItemRemove(diff_col_records[i-1].line+diff_col_records[i].line)
                                diff_col_records[i-1] = DiffItemKeep('')
                    diff_col_records = filter(lambda e:(len(e.line)>0),diff_col_records)
                    # get updated labels; yeah generally ugly code sorry
                    for diff_part in diff_col_records:
                        cell_contents_upd_lmdd = '{prev_str}{append_part}'.format(
                            prev_str = cell_contents_upd_lmdd,
                            append_part = (
                                escape_html(diff_part.line)
                                if isinstance(diff_part, DiffItemKeep)
                                else (
                                    ''
                                    if isinstance(diff_part, DiffItemInsert)
                                    else '<<REMOVED>>{ins}<<ENDREMOVED>>'.format(ins=escape_html(diff_part.line))
                                )
                            )
                        )
                        cell_contents_upd_rmdd = '{prev_str}{append_part}'.format(
                            prev_str = cell_contents_upd_rmdd,
                            append_part = (
                                escape_html(diff_part.line)
                                if isinstance(diff_part, DiffItemKeep)
                                else (
                                    '<<ADDED>>{ins}<<ENDADDED>>'.format(ins=escape_html(diff_part.line))
                                    if isinstance(diff_part, DiffItemInsert)
                                    else ''
                                )
                            )
                        )
                        if not isinstance(diff_part, DiffItemKeep):
                            did_col_change = True
                            if is_col_significant:
                                did_significant_col_change = True
                    reportline_row_lmdd[col_num] = cell_contents_upd_lmdd
                    reportline_row_rmdd[col_num] = cell_contents_upd_rmdd
                    did_any_col_change = did_any_col_change or did_col_change
                    did_any_significant_col_change = did_any_significant_col_change or did_significant_col_change
                else:
                    raise Exception('cell contents, wrong data type (not a string); the row is {item_name}'.format(item_name=item_name))

            diff_flag = ( 'diff' if did_any_significant_col_change else ( 'matches' if (not diff_flag or re.match(r'^\s*?\?*?\s*?$',diff_flag)) else diff_flag ) )

        # variable that holds row that will be added to the report
        # as mentioned above, the first cell is an indication if it was aaded, removed, then come question name, then other labels and fields
        report_line = [ diff_flag, item_name, *reportline_row_lmdd, *reportline_row_rmdd ]

        # now add the append that "report_line" variable to
        records.append(report_line)

    # add "records" to the report
    result['Records'] = records
    print('Done. Writing result...\n')

    # and return the report in json
    return json.dumps(result)



if __name__ == "__main__":
	start_time = datetime.utcnow()
	input_json_lmdd = None
	input_json_rmdd = None
	if len(sys.argv)>2:
		input_json_lmdd = sys.argv[1]
		input_json_rmdd = sys.argv[2]
	if (input_json_lmdd==None) or (input_json_rmdd==None):
		raise Exception("MDM Diff: Input files are not specified")
	if ((not os.path.isfile(input_json_lmdd)) or (not os.path.isfile(input_json_rmdd))):
		raise Exception("MDM Diff: Input file is missing")
	print("Creating diffed data...\n")
	print("Loading input JSON data...\n")
	f_lmdd = open(input_json_lmdd)
	f_rmdd = open(input_json_rmdd)
	print("Reading JSON...\n")
	report_lmdd = json.load(f_lmdd)
	report_rmdd = json.load(f_rmdd)
	print("Working...\n")
	output = find_diff_jsonstr(report_lmdd,report_rmdd)
	report_file_name = 'report.diff-report.{mdd_lmdd}-{mdd_rmdd}.json'.format(
        mdd_lmdd = re.sub(r'^\s*?report\.','',re.sub(r'\.json\s*?$','',input_json_lmdd)),
        mdd_rmdd = re.sub(r'^\s*?report\.','',re.sub(r'\.json\s*?$','',input_json_rmdd))
    )
	print("Writing results...\n")
	with open(report_file_name,'w') as output_file:
		output_file.write(output)
	end_time = datetime.utcnow()
	#elapsed_time = end_time - start_time
	print("Finished") # + str(elapsed_time)
