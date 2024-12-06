
from datetime import datetime, timezone
import json


JSON_TEMPLATE = r'''
{
    "report_type": "TextFile",
    "source_file": "insert",
    "report_datetime_utc": "insert",
    "report_datetime_local": "insert",
    "source_file_metadata": [],
    "report_scheme": {
        "columns": [
            "rawtextcontents"
        ],
        "column_headers": {
            "rawtextcontents": "File Contents"
        },
        "flags": [ "data-type:text" ]
    },
    "sections": [
        {
            "name": "filecontents",
            "content": [
                {
                    "name": "",
                    "rawtextcontents": "insert"
                }
            ]
        }
    ]
}
'''

def read(textfilecontents,added_data):

    inp_file = added_data['filename']

    data=json.loads(JSON_TEMPLATE)
    
    data['source_file']='{f}'.format(f=inp_file)
    data['report_datetime_utc']='{f}'.format(f=(datetime.now()).astimezone(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),)
    data['report_datetime_local']='{f}'.format(f=(datetime.now()).strftime('%Y-%m-%dT%H:%M:%SZ'))

    data['sections'][0]['content'][0]['rawtextcontents'] = textfilecontents

    return data
