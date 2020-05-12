This CLI was created to automate the process of adding devices to Check_MK's monitoring tool via their web API. Other functionalities include editing, deleting and viewing devices. This was done to create a more efficient means of querying and modifying the monitoring tool, as the alternative GUI solution was not satisfactory. 

The python file was generated from a j2 template using the Ansible automation tool in order to generate the CLI to be specific to your site including the IP to address the requests to. This solution is suggested as a proof of concept but more secure methods of storing the IP and secret are strongly suggested. 

The CLI was designed to be interactive including giving colored cues, thorough feedback and autocompletion features. 
