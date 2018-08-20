#TODO give valid options for eg. tag_agent: cmk-agent, ping...
# ^ can be done by first getting all hosts from site and saving all current values? works for folders but not necessarily sites/tags...
# ^ where are host_tags kept in the file system?
#TODO what if the user wants to add the host to the home directory
#TODO add some kind of logging/security

# Script to use Check_MK's web API to manipulate hosts on a site


import requests
import ast
import pprint

#acting on destination site
#need to append action to url and required attributes for use
url = "http://172.23.240.169/test_site/check_mk/webapi.py?_username=automation&_secret=17f85ba2-bb76-4fc8-86f6-0d969d9ee7b0&request_format=python&output_format=python&action="
url_actions = {"add":"add_host", \
               "services":"discover_services", \
               "edit":"edit_host", \
               "view":"get_host", \
               "view all":"get_all_hosts", \
               "delete":"delete_host", \
               "activate":"activate_changes", \
               "folders":"get_all_folders", \
               "hosttags":"get_hosttags"}

class color:
    OK = '\x1b[1;32;40m'
    ALERT = '\x1b[1;31;40m'
    END = '\x1b[0m'
    MAN = '\x1b[1;37;40m'
    HL = '\x1b[1;36;40m'


man_string = '5 instruction types: man, add, edit, view and delete\n\
 \n\
 Type man to view this instruction set.\n\
 \n\
 Use add with the following format to add hosts to the site (services included):\n\
 '+color.HL+'    add hostname  ip/alias       tag agent   path/folder  site'+color.MAN+'\n\
  eg.add vm1       172.23.240.128 cmk-agent   linux        test_site\n\
 \n\
 Use edit with the following format to edit existing hosts (one tag at a time):\n\
 '+color.HL+'    edit hostname   tag name   tag value'+color.MAN+'\n\
  eg.edit vm1        tag-os     rhel7x\n\
 \n\
 Use view to see host tag values; type "view all" or specify a host as follows:\n\
 '+color.HL+'    view hostname'+color.MAN+'\n\
  eg.view vm1\n\
 \n\
 Use delete with the following format to remove existing hosts:\n\
 '+color.HL+'    delete hostname imsure'+color.MAN+'\n\
  eg.delete vm1 imsure\n\
 \n\
 \n\
 Valid tag agents include "cmk-agent", "snmp-only" and "ping"\n\
 Hosts added with snmp-only tag will be given the default community string public.\n\
 \n\
 Valid editable tags include ipaddress, alias, tag_agent, site, snmp_community, \n\
  and any tags created on the GUI.\n\
 '



#Process GET response; report to stdout
def check_print(type, host, _response):
    response = ast.literal_eval(_response.text)
    if response['result_code'] != 0:
        print type, host, color.ALERT + response['result'] + color.END
        return False
    else:
        print type, host, color.OK + "OK" + color.END
        return True


def services(host):
    #Send GET request for services
    services_url = url+url_actions["services"]+'&request={\'hostname\': \''+host+"\'}"
    put_response = requests.get(services_url, verify=False)
    check_print("SERVICES", host, put_response)

def add_host(host_tuple):
    if len(host_tuple) != 6:
        print "Incorrect number of arguments"
        return 

    
    if host_tuple[3] == "agent":
        snmp_community = 'None'
        tag_agent = 'cmk-agent'
        tag_snmp = 'no-snmp'
    elif host_tuple[3] == "snmp":
        snmp_community = 'public'
        tag_agent = 'no-agent'
        tag_snmp = 'snmp-v2'
    else:
        print "Valid tags are 'agent' and 'snmp'"
        return

    request_str = "&request={'attributes': {'tag_agent': '"+tag_agent+\
          "', 'tag_snmp': '"+tag_snmp+"', 'snmp_community': '"+snmp_community+\
          "', 'alias': '"+host_tuple[2]+\
          "', 'site': '"+host_tuple[5]+"', 'ipaddress': '"+host_tuple[2]+\
          "'}, 'hostname': '"+host_tuple[1]+"', 'folder': '"+host_tuple[4]+"'}"

    add_url = url+url_actions["add"]+request_str
    add_response = requests.get(add_url, verify=False)
    added_eh = check_print("ADD", host_tuple[1], add_response)
    if added_eh:
        services(host_tuple[1])

def view_host(host_tuple):
    if len(host_tuple) != 2:
        print "Incorrect number of arguments"
        return

    if host_tuple[1] == "all":
        view_url = url+url_actions["view all"]
        view_response = requests.get(view_url, verify=False)
        check_print("VIEW", host_tuple[1], view_response)
        pprint.pprint(ast.literal_eval(view_response.text)['result'])

    else:
        view_url = url+url_actions["view"]+"&hostname="+host_tuple[1]
        view_response = requests.get(view_url, verify=False)
        check_print("VIEW", host_tuple[1], view_response)
        pprint.pprint(ast.literal_eval(view_response.text)['result'])

def edit_host(host_tuple):
    if len(host_tuple) != 4:
        print "Incorrect number of arguments"
        return
    
    tag_name = host_tuple[2]
    tag_value = host_tuple[3]
    request_str = "&request={'attributes': {'"+tag_name+"': '"+tag_value+"'}}"

    edit_url = url+url_actions["edit"]+"&hostname="+host_tuple[1]+request_str
    edit_response = requests.get(edit_url, verify=False)
    check_print("EDIT", host_tuple[1], edit_response)

def delete_host(host_tuple):
    if len(host_tuple) != 3:
        print "Incorrect number of arguments"
        return
    elif host_tuple[2] != "imsure":
        print "You are not sure enough"
        return

    delete_url = url+url_actions["delete"]+"&hostname="+host_tuple[1]
    delete_response = requests.get(delete_url, verify=False)
    check_print("DELETE", host_tuple[1], delete_response)

def activate():
    print "\nActivating..."
    
    #Activating changes
    activate_response = requests.get(url+url_actions["activate"], verify=False)
    check_print("ACTIVATION", "HOSTS", activate_response)

def services_host(instr_tuple):
    if len(instr_tuple) != 2:
       print "Incorrect number of arguments"
       return
    services(instr_tuple[1])

def populate():
    populate_response = requests.get(url+url_actions["folders"], verify=False)
    folders = ast.literal_eval(populate_response.text)['result']
    pprint.pprint(folders)
    for i in folders:
        print i
    
    #populate_response = requests.get(url+url_actions["hosttags"], verify=False)
    #pprint.pprint(ast.literal_eval(populate_response.text)['result']['tag_groups'][2])


populate()        

print color.MAN
print "Add, edit, view and delete hosts on site."
print "Type exit to leave. Changes will be activated upon exit."
print "Type man to view instruction set."
print color.END

instruction = ""

# Parses input, sends request to add and do service discovery
while instruction.lower() != "exit":

    instruction = raw_input("\n> ").lower()
    instr_tuple = instruction.split()
   
    if instr_tuple[0] == "man":
        print color.MAN + man_string + color.END
    elif instr_tuple[0] == "add":
        add_host(instr_tuple)
    elif instr_tuple[0] == "edit":
        edit_host(instr_tuple)
    elif instr_tuple[0] == "view":
        view_host(instr_tuple) 
    elif instr_tuple[0] == "delete":
        delete_host(instr_tuple)
    elif instr_tuple[0] == "activate":
        activate()
    elif instr_tuple[0] == "services":
        services_host(instr_tuple) 
    elif instr_tuple[0] == "exit":
        break
    else:
        print "Invalid instruction keyword"

activate()
