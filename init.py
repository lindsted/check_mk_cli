
import readline
import requests
import ast
import pprint
import cmd
import sys

url = "http://172.23.240.169/test_site/check_mk/webapi.py?_username=automation&_secret=b2b3b863-dbb5-4a20-9897-6488250c83d3&request_format=python&output_format=python&action="

class color:
    OK = '\x1b[1;32;40m'
    ALERT = '\x1b[1;31;40m'
    END = '\x1b[0m'
    MAN = '\x1b[1;37;40m'
    HL = '\x1b[1;36;40m'


# Process GET response; report to stdout
def check_print(type, host, _response):
    response = ast.literal_eval(_response.text)
    if response['result_code'] != 0:
        print type, host, color.ALERT + response['result'] + color.END
        return False
    else:
        print type, host, color.OK + "OK" + color.END
        return True


def add_tag():

    args = "&request={'aux_tags':[], 'tag_groups':[{'title':'Operating Systems','id':'os',\
'tags':[{'id':'noos','title':'No Operating System'}]}]}"
    view_url = url+"set_hosttags"
    view_response = requests.get(view_url, verify=False)
    check_print("ADD", "TAGS", view_response)
    pprint.pprint(ast.literal_eval(view_response.text)['result'])

add_tag()

