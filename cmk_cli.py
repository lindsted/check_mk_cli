#TODO add some kind of logging/security

# Script to use Check_MK's web API to manipulate hosts on a site

import readline
import requests
import ast
import pprint
import cmd

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
    if len(host_tuple) != 5:
        print "Incorrect number of arguments"
        return 

    # translating agent tags    
    if host_tuple[2] == "agent":
        snmp_community = 'None'
        tag_agent = 'cmk-agent'
        tag_snmp = 'no-snmp'
    elif host_tuple[2] == "snmp":
        snmp_community = 'public'
        tag_agent = 'no-agent'
        tag_snmp = 'snmp-v2'
    else:
        print "Valid tags are 'agent' and 'snmp'"
        return

    # translating folder tag
    if host_tuple[3] == "main":
        host_tuple[3] = ''

    request_str = "&request={'attributes': {'tag_agent': '"+tag_agent+\
          "', 'tag_snmp': '"+tag_snmp+"', 'snmp_community': '"+snmp_community+\
          "', 'alias': '"+host_tuple[1]+\
          "', 'site': '"+host_tuple[4]+"', 'ipaddress': '"+host_tuple[1]+\
          "'}, 'hostname': '"+host_tuple[0]+"', 'folder': '"+host_tuple[3]+"'}"

    add_url = url+url_actions["add"]+request_str
    add_response = requests.get(add_url, verify=False)
    added_eh = check_print("ADD", host_tuple[0], add_response)
    if added_eh:
        services(host_tuple[0])

def view_host(host_tuple):
    if len(host_tuple) != 1:
        print "Incorrect number of arguments"
        return

    if host_tuple[0] == "all":
        view_url = url+url_actions["view all"]
        view_response = requests.get(view_url, verify=False)
        check_print("VIEW", host_tuple[0], view_response)
        pprint.pprint(ast.literal_eval(view_response.text)['result'])

    else:
        view_url = url+url_actions["view"]+"&hostname="+host_tuple[0]
        view_response = requests.get(view_url, verify=False)
        check_print("VIEW", host_tuple[0], view_response)
        pprint.pprint(ast.literal_eval(view_response.text)['result'])

def edit_host(host_tuple):
    if len(host_tuple) != 3:
        print "Incorrect number of arguments"
        return
    
    tag_name = host_tuple[1]
    tag_value = host_tuple[2]
    request_str = "&request={'attributes': {'"+tag_name+"': '"+tag_value+"'}}"

    edit_url = url+url_actions["edit"]+"&hostname="+host_tuple[0]+request_str
    edit_response = requests.get(edit_url, verify=False)
    check_print("EDIT", host_tuple[0], edit_response)

def delete_host(host_tuple):
    if len(host_tuple) != 2:
        print "Incorrect number of arguments"
        return
    elif host_tuple[1] != "imsure":
        print "You are not sure enough"
        return

    delete_url = url+url_actions["delete"]+"&hostname="+host_tuple[0]
    delete_response = requests.get(delete_url, verify=False)
    check_print("DELETE", host_tuple[0], delete_response)

def activate():
    activate_response = requests.get(url+url_actions["activate"], verify=False)
    check_print("ACTIVATION", "HOSTS", activate_response)

def services_host(instr_tuple):
    if len(instr_tuple) != 1:
       print "Incorrect number of arguments"
       return
    services(instr_tuple[0])

hosts = []
folders = ["main"]
sites = [] 
tags = {}
ips = ["172.30."]
agents = ["snmp", "agent"] 


# On start-up, fill global variables with site's existing values 
# For auto-completion interface
def populate():
    populate_response = requests.get(url+url_actions["view all"], verify=False)
    raw_hosts = ast.literal_eval(populate_response.text)['result']
    for host in raw_hosts:
        hosts.append(host)
    
    # sites is populated based on existing values
    temp_set = set()
    for host in raw_hosts:
        temp_set.add( raw_hosts[host]['attributes']['site'] )
    sites.extend(list(temp_set))

    populate_response = requests.get(url+url_actions["folders"], verify=False)
    raw_folders = ast.literal_eval(populate_response.text)['result']
    for folder in raw_folders:
        folders.append(folder)
    
    populate_response = requests.get(url+url_actions["hosttags"], verify=False)
    raw_tags = (ast.literal_eval(populate_response.text)['result']['tag_groups'][2:])
    for tag in raw_tags:
        temp_list = []      
        for i in tag["tags"]:
            temp_list.append(i["id"])
        tags[ "tag_"+tag["id"] ] = temp_list



# For tab auto-complete feature
# Fn general, each command has a do and a complete function
#       when enter is pressed, do is executed; when tab, complete
# The string in the do function is used as the help entry for the command
class MyCmd(cmd.Cmd):
    intro = '\nCLI leveraging Check_MK\'s Web-API. \nType ? <keyword> for more info.' 
    prompt = '> '


    def do_add(self, line):
        'add hostname ip tag_agent folder site \n Type main for home directory placement \
         Also completes services on newly added hosts'
        add_host(line.split())
    def complete_add(self, text, line, start_index, end_index):
        args = line.split()
        if text:
            if len(args) == 2:
                return [
                    host for host in hosts
                    if host.startswith(text)
                ]
            elif len(args) == 3:
                return [
                    ip for ip in ips
                    if ip.startswith(text)
                ] 
            elif len(args) == 4:
                return [
                    agent for agent in agents
                    if agent.startswith(text)
                ]
            elif len(args) == 5:
                return [
                    folder for folder in folders
                    if folder.startswith(text)
                ]
            elif len(args) == 6:
                return [
                    site for site in sites
                    if site.startswith(text)
                ]
        else:
            if len(args) == 1:
                return hosts
            elif len(args) == 2:
                return ips
            elif len(args) == 3:
                return agents
            elif len(args) == 4:
                return folders
            elif len(args) == 5:
                return sites

    def do_edit(self, line):
        'edit hostname tag_name tag_value'
        edit_host(line.split())            
    def complete_edit(self, text, line, start_index, end_index):
        args = line.split()        
        if text:
	    if len(args) == 2:
                return [
                    host for host in hosts
                    if host.startswith(text)
                ]
            elif len(args) == 3:
                return [
                    tag for tag in tags
                    if tag.startswith(text)
                ]
            elif len(args) == 4:
                return [
                    value for value in tags[args[2]]
                    if value.startswith(text)
                ]
        else:
            if len(args) == 1:
                return hosts
            elif len(args) == 2:
                return [tag for tag in tags]
            elif len(args) == 3:
                return [ value for value in tags[args[2]] ]   
    
    def do_view(self, line):
        'view hostname (or all)'
        view_host(line.split())
    def complete_view(self, text, line, start_index, end_index):
        if text:
            return [
                host for host in ( hosts+["all"] )
                if host.startswith(text)
            ]
        else: 
            return hosts+["all"]

    def do_delete(self, line):
        'delete hostname imsure (to acknowledge the finality of the action)'
        delete_host(line.split())
    def complete_delete(self, text, line, start_index, end_index):
        if text:
            return [
                host for host in hosts
                if host.startswith(text)
            ]
        else:
            return hosts

    def do_services(self, line):
        'services hostname'    
        services_host(line.split())
    def complete_services(self, text, line, start_index, end_index):
        if text:
            return [
                host for host in hosts
                if host.startswith(text)
            ]
        else:
            return hosts

    def do_activate(self, line):
        'activate'
        activate()

    def do_exit(self, line):
        'exit (activates and exits programs)'
        print "\nActivating..."
        activate()
        return True

    def do_EOF(self, line):
        'EOF exits without activating'
        print
        return True



if __name__ == '__main__':
    populate()
    my_cmd = MyCmd()
    my_cmd.cmdloop()
        
