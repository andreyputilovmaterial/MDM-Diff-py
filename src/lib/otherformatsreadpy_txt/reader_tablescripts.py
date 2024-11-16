
import re
import json
from datetime import datetime, timezone





# class TableSplitter:
#     def __init__(self,data):
#         self.data = data
#         self.pos = None
#         self.start = None
#         self.need_reiterate = None
#         self.delimiter = r"^\s*?'{10}'*?\s*?\n\s*?'{3}[^\n]*?\s*?\n\s*?'{10}'*?\s*?\n"
        
#     def find_next_delimniter_pos(self):
#         match = re.search(self.delimiter,self.data[self.pos:],flags=re.M|re.DOTALL|re.I)
#         if match:
#             return match.start(0) + self.pos
#         else:
#             return -1
#     def __iter__(self):
#         self.start = None
#         self.pos = self.find_next_delimniter_pos()
#         self.need_reiterate = 0
#         return self
#     def __next__(self):
#         if len(self.data)==0:
#             raise StopIteration
#         elif self.pos<0:
#             if self.start>=len(self.data):
#                 raise StopIteration
#             else:
#                 part = self.data[self.start:]
#                 self.start = len(self.data)
#                 return part
#         else:
#             part = self.data[self.start:self.pos]
#             matches_settable_pattern = re.findall(r"^\s*?set\b\s*?\btable\s*?=.*?",part,flags=re.M|re.DOTALL|re.I)
#             if not matches_settable_pattern:
#                 self.need_reiterate = 0
#             elif len(matches_settable_pattern)==1:
#                 self.need_reiterate = 0
#             elif len(matches_settable_pattern)>1:
#                 #the tricky one
#                 total_settable_pattern_counts = len(matches_settable_pattern)
#                 processed_settable_pattern_counts = self.need_reiterate
#                 if processed_settable_pattern_counts >= total_settable_pattern_counts:
#                     pass
#                 else:
#                     TBD...
#             else:
#                 raise AttributeError('what?')
#             self.start = self.pos
#             self.pos = self.find_next_delimiter_pos()
#             return part


class TableSplitter:
    def __init__(self,data):
        self.data = data
        self.delimiter = r"^\s*?'{10}'*?\s*?\n\s*?'{3}[^\n]*?\s*?\n\s*?'{10}'*?\s*?\n"
        
    def __iter__(self):
        delimiters = re.finditer(self.delimiter,self.data,flags=re.M|re.DOTALL|re.I)
        delimiters = [ delim.start(0) for delim in delimiters ]
        parts = []
        start = 0
        for delim in delimiters:
            pos = delim
            parts.append(self.data[start:pos])
            start = pos
        return iter(parts)





def syntaxextractor_title_comment(txt,fields):
    name = 'title_comment'
    matches = re.match("^\s*?'{10}'*?\s*?\n\s*?'{3}'*\s*([^\n]*?)\s*?\n\s*?'{10}'*?\s*?\n.*?$",txt,flags=re.M|re.DOTALL|re.I)
    result = None
    if matches:
        result = matches[1]
    return name,result

def syntaxextractor_comments(txt,fields):
    name = 'comments'
    matches = re.match(r"^(\s*?'{10}'*?\s*?\n\s*?'{3}'*\s*[^\n]*?\s*?\n\s*?'{10}'*?\s*?\n)((?:\s*?'[^\n]*?\s*?\n)*)((?:\s*?[^\n]*?\s*?\n)*?)((?:\s*?set\b\s*?\btable\s*?=[^\n]*?\s*?\n)?)((?:\s*?[^\n]*?\s*?\n)*)$",txt,flags=re.M|re.DOTALL|re.I)
    result = None
    if matches:
        result = matches[2]
    return name,result

def syntaxextractor_tablecode(txt,fields):
    name = 'tablecode'
    matches = re.match(r"^(\s*?'{10}'*?\s*?\n\s*?'{3}'*\s*[^\n]*?\s*?\n\s*?'{10}'*?\s*?\n)((?:\s*?'[^\n]*?\s*?\n)*)((?:\s*?[^\n]*?\s*?\n)*?)((?:\s*?set\b\s*?\btable\s*?=[^\n]*?\s*?\n)?)((?:\s*?[^\n]*?\s*?\n)*)$",txt,flags=re.M|re.DOTALL|re.I)
    result = None
    if matches:
        result = matches[4]
    return name,result

def syntaxextractor_tablecode_leadinglines(txt,fields):
    name = 'tablecode_leadinglines'
    matches = re.match(r"^(\s*?'{10}'*?\s*?\n\s*?'{3}'*\s*[^\n]*?\s*?\n\s*?'{10}'*?\s*?\n)((?:\s*?'[^\n]*?\s*?\n)*)((?:\s*?[^\n]*?\s*?\n)*?)((?:\s*?set\b\s*?\btable\s*?=[^\n]*?\s*?\n)?)((?:\s*?[^\n]*?\s*?\n)*)$",txt,flags=re.M|re.DOTALL|re.I)
    result = None
    if matches:
        result = matches[3]
    return name,result

def syntaxextractor_tablecode_trailinglines(txt,fields):
    name = 'tablecode_trailinglines'
    matches = re.match(r"^(\s*?'{10}'*?\s*?\n\s*?'{3}'*\s*[^\n]*?\s*?\n\s*?'{10}'*?\s*?\n)((?:\s*?'[^\n]*?\s*?\n)*)((?:\s*?[^\n]*?\s*?\n)*?)((?:\s*?set\b\s*?\btable\s*?=[^\n]*?\s*?\n)?)((?:\s*?[^\n]*?\s*?\n)*)$",txt,flags=re.M|re.DOTALL|re.I)
    result = None
    if matches:
        result = matches[5]
    return name,result

def syntaxextractor_table_title(txt,fields):
    name = 'table_title'
    result = None
    matches = None
    if fields['tablecode']:
        matches = re.match(r"^\s*?set\b\s*?\btable\s*?=\s*?createtable\s*?\(\s*?\w+\s*?,\s*?\w+\s*?,\s*?[^,]*?\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s].*?)\s*?,\s*?([^\s][^,]*?)\s*?\)\s*?(?:'[^\n]*?)?\s*?\n",fields['tablecode'],flags=re.M|re.DOTALL|re.I)
        if not matches:
            matches = re.match(r"^\s*?set\b\s*?\btable\s*?=\s*?creategridslicetable\s*?\(\s*?\w+\s*?,\s*?\w+\s*?,\s*?[^,]*?\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s].*?)\s*?,\s*?([^\s][^,]*?)\s*?\)\s*?(?:'[^\n]*?)?\s*?\n",fields['tablecode'],flags=re.M|re.DOTALL|re.I)
        if not matches:
            matches = re.match(r"^\s*?set\b\s*?\btable\s*?=\s*?tabledoc.tables.addnew\s*?\(\s*?([^\s][^,]*?)\s*?,\s*?(([^\s].*?))\s*?,\s*?([^\s][^,]*?)\s*?\)\s*?(?:'[^\n]*?)?\s*?\n",fields['tablecode'],flags=re.M|re.DOTALL|re.I)
        if not matches:
            matches = re.match(r"^\s*?set\b\s*?\btable\s*?=\s*?create\w*table\s*?\(\s*?\w+\s*?,\s*?\w+\s*?,\s*?[^,]*?\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s].*?)\s*?,\s*?([^\s][^,]*?)\s*?\)\s*?(?:'[^\n]*?)?\s*?\n",fields['tablecode'],flags=re.M|re.DOTALL|re.I)
        if matches:
            result = matches[4]
    return name,result

def syntaxextractor_table_axis(txt,fields):
    name = 'table_axis'
    result = None
    matches = None
    if fields['tablecode']:
        matches = re.match(r"^\s*?set\b\s*?\btable\s*?=\s*?createtable\s*?\(\s*?\w+\s*?,\s*?\w+\s*?,\s*?[^,]*?\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s].*?)\s*?,\s*?([^\s][^,]*?)\s*?\)\s*?(?:'[^\n]*?)?\s*?\n",fields['tablecode'],flags=re.M|re.DOTALL|re.I)
        if not matches:
            matches = re.match(r"^\s*?set\b\s*?\btable\s*?=\s*?creategridslicetable\s*?\(\s*?\w+\s*?,\s*?\w+\s*?,\s*?[^,]*?\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s].*?)\s*?,\s*?([^\s][^,]*?)\s*?\)\s*?(?:'[^\n]*?)?\s*?\n",fields['tablecode'],flags=re.M|re.DOTALL|re.I)
        if not matches:
            matches = re.match(r"^\s*?set\b\s*?\btable\s*?=\s*?tabledoc.tables.addnew\s*?\(\s*?([^\s][^,]*?)\s*?,\s*?(([^\s].*?))\s*?,\s*?([^\s][^,]*?)\s*?\)\s*?(?:'[^\n]*?)?\s*?\n",fields['tablecode'],flags=re.M|re.DOTALL|re.I)
        if not matches:
            matches = re.match(r"^\s*?set\b\s*?\btable\s*?=\s*?create\w*table\s*?\(\s*?\w+\s*?,\s*?\w+\s*?,\s*?[^,]*?\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s].*?)\s*?,\s*?([^\s][^,]*?)\s*?\)\s*?(?:'[^\n]*?)?\s*?\n",fields['tablecode'],flags=re.M|re.DOTALL|re.I)
        if matches:
            result = matches[3]
    return name,result

def syntaxextractor_table_variable(txt,fields):
    name = 'table_variable'
    result = None
    matches = None
    if fields['tablecode']:
        matches = re.match(r"^\s*?set\b\s*?\btable\s*?=\s*?createtable\s*?\(\s*?\w+\s*?,\s*?\w+\s*?,\s*?[^,]*?\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s].*?)\s*?,\s*?([^\s][^,]*?)\s*?\)\s*?(?:'[^\n]*?)?\s*?\n",fields['tablecode'],flags=re.M|re.DOTALL|re.I)
        if not matches:
            matches = re.match(r"^\s*?set\b\s*?\btable\s*?=\s*?creategridslicetable\s*?\(\s*?\w+\s*?,\s*?\w+\s*?,\s*?[^,]*?\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s].*?)\s*?,\s*?([^\s][^,]*?)\s*?\)\s*?(?:'[^\n]*?)?\s*?\n",fields['tablecode'],flags=re.M|re.DOTALL|re.I)
        if not matches:
            matches = re.match(r"^\s*?set\b\s*?\btable\s*?=\s*?tabledoc.tables.addnew\s*?\(\s*?([^\s][^,]*?)\s*?,\s*?(([^\s].*?))\s*?,\s*?([^\s][^,]*?)\s*?\)\s*?(?:'[^\n]*?)?\s*?\n",fields['tablecode'],flags=re.M|re.DOTALL|re.I)
        if not matches:
            matches = re.match(r"^\s*?set\b\s*?\btable\s*?=\s*?create\w*table\s*?\(\s*?\w+\s*?,\s*?\w+\s*?,\s*?[^,]*?\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s].*?)\s*?,\s*?([^\s][^,]*?)\s*?\)\s*?(?:'[^\n]*?)?\s*?\n",fields['tablecode'],flags=re.M|re.DOTALL|re.I)
        if matches:
            result = matches[2]
    return name,result

def syntaxextractor_table_id(txt,fields):
    name = 'table_id'
    result = None
    matches = None
    if fields['tablecode']:
        matches = re.match(r"^\s*?set\b\s*?\btable\s*?=\s*?createtable\s*?\(\s*?\w+\s*?,\s*?\w+\s*?,\s*?[^,]*?\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s].*?)\s*?,\s*?([^\s][^,]*?)\s*?\)\s*?(?:'[^\n]*?)?\s*?\n",fields['tablecode'],flags=re.M|re.DOTALL|re.I)
        if not matches:
            matches = re.match(r"^\s*?set\b\s*?\btable\s*?=\s*?creategridslicetable\s*?\(\s*?\w+\s*?,\s*?\w+\s*?,\s*?[^,]*?\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s].*?)\s*?,\s*?([^\s][^,]*?)\s*?\)\s*?(?:'[^\n]*?)?\s*?\n",fields['tablecode'],flags=re.M|re.DOTALL|re.I)
        if not matches:
            matches = re.match(r"^\s*?set\b\s*?\btable\s*?=\s*?tabledoc.tables.addnew\s*?\(\s*?([^\s][^,]*?)\s*?,\s*?(([^\s].*?))\s*?,\s*?([^\s][^,]*?)\s*?\)\s*?(?:'[^\n]*?)?\s*?\n",fields['tablecode'],flags=re.M|re.DOTALL|re.I)
        if not matches:
            matches = re.match(r"^\s*?set\b\s*?\btable\s*?=\s*?create\w*table\s*?\(\s*?\w+\s*?,\s*?\w+\s*?,\s*?[^,]*?\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s][^,]*?)\s*?,\s*?([^\s].*?)\s*?,\s*?([^\s][^,]*?)\s*?\)\s*?(?:'[^\n]*?)?\s*?\n",fields['tablecode'],flags=re.M|re.DOTALL|re.I)
        if matches:
            result = matches[1]
    return name,result

def syntaxextractor_table_addedrules(txt,fields):
    name = 'table_addedrules'
    result = None
    if fields['tablecode_trailinglines']:
        lines = fields['tablecode_trailinglines'].split('\n')
        lines = [ line for line in lines if re.match(r'^\s*?table\..*?',line,flags=re.I) ]
        if len(lines)>0:
            result = '\n'.join(lines)
    return name,result

def syntaxextractor_table_filters(txt,fields):
    name = 'table_filters'
    result = None
    if fields['tablecode_trailinglines']:
        lines = fields['tablecode_trailinglines'].split('\n')
        lines = [ line for line in lines if re.match(r'^\s*?table\..*?',line,flags=re.I) ]
        lines_filters = []
        for line in lines:
            matches = re.match(r'^\s*?table\.filters\.addnew\s*?\(\s*?"[^"]*?"\s*?,\s*?([^\n]*?)\s*?,\s*?".*?"\s*?\)\s*?(?:\'[^\n]*?)?\s*?$',line,flags=re.I)
            if matches:
                lines_filters.append(matches[1])
        if len(lines_filters)>0:
            result = '\n'.join(lines_filters)
    return name,result





syntaxextractors = [
    syntaxextractor_title_comment,
    syntaxextractor_comments,
    syntaxextractor_tablecode,
    syntaxextractor_tablecode_leadinglines,
    syntaxextractor_tablecode_trailinglines,
    syntaxextractor_table_title,
    syntaxextractor_table_axis,
    syntaxextractor_table_id,
    syntaxextractor_table_addedrules,
    syntaxextractor_table_filters,
]






def read(textfilecontents,added_data):

    inp_file = added_data['filename']

    data=json.loads('{ "report_type": "TextFile", "source_file": "insert", "report_datetime_utc": "insert", "report_datetime_local": "insert", "source_file_metadata": [ ], "report_scheme": { "columns": [ "rawtextcontents" ], "column_headers": { "rawtextcontents": "File Contents" }, "flags": [] }, "sections": [ { "name": "filecontents", "content": [] } ] }')
    
    data['source_file']='{f}'.format(f=inp_file)
    data['report_datetime_utc']='{f}'.format(f=(datetime.now()).astimezone(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),)
    data['report_datetime_local']='{f}'.format(f=(datetime.now()).strftime('%Y-%m-%dT%H:%M:%SZ'))

    data['sections'][0]['name'] = 'tables_definitions'

    column_specs = ['name','rawtextcontents']

    parts = TableSplitter(textfilecontents)
    table_number = 0
    for part in parts:
        def normalizelinebreaks(txt):
            return re.sub(
                r'("!)(.*?)(!")',
                lambda m: '{opening}{content_escaped}{closingpart}'.format(opening=m[1],closingpart=m[3],content_escaped=re.sub(r'[\n]','\\\\n',m[2],flags=re.M|re.DOTALL|re.I)),
                re.sub(
                    r"('!)(.*?)(!')",
                    lambda m: '{opening}{content_escaped}{closingpart}'.format(opening=m[1],closingpart=m[3],content_escaped=re.sub(r'[\n]','\\\\n',m[2],flags=re.M|re.DOTALL|re.I)),
                    txt,
                    flags=re.M|re.DOTALL|re.I
                ),
                flags=re.M|re.DOTALL|re.I
            )
        part = normalizelinebreaks(part)
        table_def = {
            'rawtextcontents': part
        }
        for syntaxparser in syntaxextractors:
            name,matching_piece = syntaxparser(part,table_def)
            table_def = {**table_def,**{name:matching_piece}}
            if not (name in column_specs):
                column_specs.append(name)

        table_def['name'] = table_def['title_comment']
        if not table_def['title_comment'] and (table_number==0):
            table_def['name'] = 'preparation_code'
        else:
            table_def['table_number'] = table_number + 1
            table_number = table_number + 1

        data['sections'][0]['content'].append(table_def)

    data['report_scheme']['columns'] = column_specs

    return data
