#TODO add some kind of logging/security

# Script to use Check_MK's Web-API to configure hosts on a site
# - Changes viewable on the multisite post activation
# - Functional for Check_MK 1.5
# - Check_MK does a majority of the error handling; printed to stdout by check_print
# - A majority of the script covers the auto-complete features

import readline
import requests
import ast
import pprint
import cmd
import sys


# Url acting on destination site
# For use, the url needs the action keyword and associated attribute values
url = "http://172.23.240.169/test_site/check_mk/webapi.py?_username=automation&_secret=b2b3b863-dbb5-4a20-9897-6488250c83d3&request_format=python&output_format=python&action="
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
    MAN = '\x1b[1;33;40m'
    HL = '\x1b[1;36;40m'


# for intro and help pages
add_man = "add <hostname> <ip> <operating system> <sql status>\n\
 Eg. add vtormtapr01 172.23.240.159 rhel7x no-sql\n"
edit_man = "edit <hostname> <tag name> <tag value>\n\
 Eg. edit vtormtapr01 tag_os rhel6x\n"
delete_man = "delete <hostname> imsure\n\
 Eg. delete vtormtapr01 imsure\n"
services_man = "services <hostname>\n\
 Eg. services vtormtapr01\n"
view_man = "view <hostname>\n\
 Eg. view vtormtapr01\n"

activate_man = "activate    activate the changes on the sites\n"
exit_man = "exit        activate changes and terminate script\n"
EOF_man = "EOF (CtrlD) terminate script without activating changes\n"
help_man = "help (or ?) repeat the specified command's args and examples\n"

intro_man = "CLI leveraging Check_MK's Web-API.\n\
\n\
Features: add, edit, view, and delete hosts. \n\
          Also completes service discovery and changes activation.\n\
          TAB and arrow keys interface implemented for autocompletion.\n"

hosts_man = add_man + edit_man + view_man + services_man
other_man = activate_man + exit_man + EOF_man + help_man
complete_man = color.HL + intro_man + "\n" + color.MAN + hosts_man + "\n" + other_man + color.END + "\n\n"



# These globals are used by the auto-complete features
# On start-up, they are filled by populate() with the destination site's existing values
# Updated as user adds / removes hosts etc.
hosts = []
folders = []
sites = ["test_site", "slave_site"]
tags = {}
ips = ["172.23."]
os_tags = ["noos", "win2k", "win2k3", "win2k8", "win2k12r2", "rhel4x", "rhel5x", "rhel6x", "rhel7x"]
locations = {"tor":"test_site", "q9b":"slave_site", "q9t":"slave_site"}




# Process GET response; report to stdout
def check_print(type, host, _response):
    response = ast.literal_eval(_response.text)
    if response['result_code'] != 0:
        print type, host, color.ALERT + response['result'] + color.END
        return False
    else:
        print type, host, color.OK + "OK" + color.END
        return True



# The following functions process user input as a tuple,
#  and send their corresponding request through

def services(host):
    services_url = url+url_actions["services"]+'&request={\'hostname\': \''+host+"\'}"
    put_response = requests.get(services_url, verify=False)
    check_print("SERVICES", host, put_response)


def add_host(host_tuple):

    # host_tuple should look like [host, ip, os, sql-server]
    if len(host_tuple) != 4:
        print "Incorrect number of arguments"
        return 
    elif len(host_tuple[0]) != 11:
        print "Host does not follow naming convention; add via GUI"
        return

    host, ip, os, sql = host_tuple[0:4]
    match_err = "Unable to resolve folder and site from hostname, no precedence set; add with complete arguments"

    loc = host[1:4]            
    app = host[4:7]
    site = locations[loc]

    if os not in os_tags:
        print "Invalid os tag"
        return
    elif os.startswith("win"):
        agent = "agent"
        os_fam = "Windows"
    elif os.startswith("rhel"):
        agent = "agent"
        os_fam = "Linux"
    elif os == "noos":
        agent = "snmp"
        os_fam = "None"


    # translating agent tags    
    if agent == "agent":        
        folder = "sys/t1/"+app+"/"+loc

        snmp_community = 'None'
        tag_agent = 'cmk-agent'
        tag_snmp = 'no-snmp'
    elif agent == "snmp":
        folder = "net/t1/"+app+"/"+loc

        snmp_community = 'public'
        tag_agent = 'no-agent'
        tag_snmp = 'snmp-v2'


    # appended to main url to specify host's attributes
    request_str = "&request={'attributes': {'tag_agent': '"+tag_agent+\
          "', 'tag_snmp': '"+tag_snmp+"', 'snmp_community': '"+snmp_community+\
          "', 'tag_os': '"+os+"', 'tag_os-family': '"+os_fam+\
          "', 'alias': '"+ip+"', 'tag_sql-server': '"+sql+\
          "', 'site': '"+site+"', 'ipaddress': '"+ip+\
          "'}, 'hostname': '"+host+"', 'folder': '"+folder+"'}"
    
    # send GET request for add; upon success also complete service discovery
    add_url = url+url_actions["add"]+request_str
    add_response = requests.get(add_url, verify=False)
    added_eh = check_print("ADD", host, add_response)
    if added_eh:
        services(host)
        
        # Update global vars
        hosts.append(host)
        if folder not in folders:
            folders.append(folder)
        if site not in sites:
            sites.append(site)
        


def view_host(host_tuple):

    # users may view "all" or a specific host
    if len(host_tuple) != 1:
        print "Incorrect number of arguments"
        return

    if host_tuple[0] == "all":
        view_url = url+url_actions["view all"]
        view_response = requests.get(view_url, verify=False)
        view_eh = check_print("VIEW", host_tuple[0], view_response)
        if view_eh:
            pprint.pprint(ast.literal_eval(view_response.text)['result'])

    else:
        view_url = url+url_actions["view"]+"&hostname="+host_tuple[0]
        view_response = requests.get(view_url, verify=False)
        view_eh = check_print("VIEW", host_tuple[0], view_response)
        if view_eh:
            pprint.pprint(ast.literal_eval(view_response.text)['result'])


def edit_host(host_tuple):

    # host_tuple should have format [host, tag_id, tag_value]
    if len(host_tuple) != 3:
        print "Incorrect number of arguments"
        return
    
    host, tag_name, tag_value = host_tuple
    request_str = "&request={'attributes': {'"+tag_name+"': '"+tag_value+"'}}"

    edit_url = url+url_actions["edit"]+"&hostname="+host+request_str
    edit_response = requests.get(edit_url, verify=False)
    check_print("EDIT", host, edit_response)


def delete_host(host_tuple):

    # host_tuple should have format [host, "imsure"]
    if len(host_tuple) != 2:
        print "Incorrect number of arguments"
        return
    elif host_tuple[1] != "imsure":
        print "You are not sure enough!"
        return

    delete_url = url+url_actions["delete"]+"&hostname="+host_tuple[0]
    delete_response = requests.get(delete_url, verify=False)
    deleted_eh = check_print("DELETE", host_tuple[0], delete_response)
    if deleted_eh:
        hosts.remove(host_tuple[0])

def activate():
    activate_response = requests.get(url+url_actions["activate"], verify=False)
    check_print("ACTIVATION", "HOSTS", activate_response)


def services_host(host_tuple):
    if len(host_tuple) != 1:
       print "Incorrect number of arguments"
       return
    services(host_tuple[0])




def populate():
    populate_response = requests.get(url+url_actions["view all"], verify=False)
    raw_hosts = ast.literal_eval(populate_response.text)['result']
    for host in raw_hosts:
        hosts.append(host)
    
    # sites is populated based on where current hosts are
    # (there may be connected sites that exist without hosts; they will not be included)
    temp_set = set()
    for host in raw_hosts:
        temp_set.add( raw_hosts[host]['attributes']['site'] )
    sites.extend(list(temp_set))

    populate_response = requests.get(url+url_actions["folders"], verify=False)
    raw_folders = ast.literal_eval(populate_response.text)['result']
    for folder in raw_folders:
        folders.append(folder)
    folders.remove("")
    
    populate_response = requests.get(url+url_actions["hosttags"], verify=False)
    raw_tags = (ast.literal_eval(populate_response.text)['result']['tag_groups'][2:])
    for tag in raw_tags:
        temp_list = []      
        for i in tag["tags"]:
            temp_list.append(i["id"])
        tags[ "tag_"+tag["id"] ] = temp_list



# For tab auto-complete feature
# In general, each command has a do and a complete function
#       when enter is pressed, do is executed; when tab, complete
# The string in the do function is used as the help entry for the command
class Command(cmd.Cmd):
    intro = complete_man 
    prompt = '> '

    def help_add(self):
        print add_man
    def do_add(self, line):
        add_host(line.lower().split())
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
                    os for os in os_tags
                    if os.startswith(text)
                ]
            elif len(args) == 5:
                return [
                    sql for sql in ["no-sql", "sql-srv"]
                    if sql.startswith(text)
                ]

        
        else:
            if len(args) == 1:
                return hosts
            elif len(args) == 2:
                return ips
            elif len(args) == 3:
                return os_tags
            elif len(args) == 4:
                return ["no-sql", "sql-srv"]

    def help_edit(self):
        print edit_man
    def do_edit(self, line):
        edit_host(line.lower().split())            
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
    
    def help_view(self):
        print view_man 
    def do_view(self, line):
        view_host(line.lower().split())
    def complete_view(self, text, line, start_index, end_index):
        if text:
            return [
                host for host in ( hosts+["all"] )
                if host.startswith(text)
            ]
        else: 
            return hosts+["all"]

    def help_delete(self):
        print delete_man
    def do_delete(self, line):
        delete_host(line.lower().split())
    def complete_delete(self, text, line, start_index, end_index):
        if text:
            return [
                host for host in hosts
                if host.startswith(text)
            ]
        else:
            return hosts

    def help_services(self):
        print services_man
    def do_services(self, line):
        services_host(line.lower().split())
    def complete_services(self, text, line, start_index, end_index):
        if text:
            return [
                host for host in hosts
                if host.startswith(text)
            ]
        else:
            return hosts

    def help_activate(self):
        print activate_man
    def do_activate(self, line):
        activate()

    def help_exit(self):
        print exit_man
    def do_exit(self, line):
        print "\nActivating..."
        activate()
        return True

    def help_EOF(self):
        print EOF_man
    def do_EOF(self, line):
        print
        return True



if __name__ == '__main__':
    # clear screen
    print "\033[H\033[J"

    populate()
    cmd = Command()
    cmd.cmdloop()
        

