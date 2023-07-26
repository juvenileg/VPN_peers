#! /bin/python
# Name: output.py
# Author: gg
# Version 1.0
# Description: Script to output a json file of connected vpn clients on a wireguard docker container
# Docker container link: https://hub.docker.com/r/linuxserver/wireguard
# This script needs to be in the /config folder, wherever that is mapped to

import json
import os
import subprocess
import re
import varo

vpns = [] #list of dictionaries
vpn = {} #my dictionary

command = 'docker exec wireguard wg show | grep -E "endpoint|allowed|latest|transfer"'
output1 = subprocess.run(command, shell=True, capture_output=True)
output1 = output1.stdout.decode()

def escape_ansi(line): #function to remove any ansi encoding
    ansi_escape =re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
    #return ansi_escape.sub('', line)
    ansi_escape = ansi_escape.sub('', line)
    return ansi_escape.replace('\r', '')
output1 = escape_ansi(output1)

match1 = re.findall('endpoint:.(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', output1)
match2 = re.findall('ips:.(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', output1)
match3 = re.findall('handshake:.(.*)', output1)
match4 = re.findall('transfer:.(.*)\s*.received', output1)
match5 = re.findall('received,.(.*)\s*.sent', output1)

#current_folder = os.getcwd() ###this script needs to be in the /config folder,wherever that is mapped to
current_folder = f'/home/{varo.user}/Drive/conf_files/wireguard_data'
files = os.listdir(current_folder)
for file in files:
    if file.startswith('peer'):
        nfile = file[5:]
        vpn = {'Server' : 'Windrush', 'Peer' : nfile}
        command = f'cat {current_folder}/{file}/{file}.conf | grep Address'
        output = subprocess.run(command, shell=True, capture_output=True)
        output = output.stdout.decode()
        match = re.search(r'\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}', output)
        for i in range(output1.count('endpoint')):
            if match.group() == match2[i]:
                minutes = 0
                for var in re.findall(r'(\d+) day', match3[i]): #extract minutes to show only peers active in the last 30 mins.
                    minutes += int(var) * 60
                for var in re.findall(r'(\d+) hour', match3[i]): #extract minutes to show only peers active in the last 30 mins.
                    minutes += int(var) * 60
                for var in re.findall(r'(\d+) minutes', match3[i]):
                    minutes += int(var)
                if minutes < 31:
                    vpn.update({'Public IP' : match1[i],'Private IP' : match2[i],'Last active' : match3[i],'upload' : match4[i],'download' : match5[i], "color": "green", "icon": "mdi:lan-connect"})
                    vpns.append(vpn)
                else:
                    vpn.update({'Public IP' : match1[i],'Private IP' : match2[i],'Last active' : match3[i],'upload' : match4[i],'download' : match5[i], "color": "#a60b00", "icon": "mdi:lan-disconnect"})
                    vpns.append(vpn)


output={}
i = 0
for item in vpns:
    i += 1
    output["d"+str(i)] = {'Server' : item['Server'], "peer": item['Peer'], "ip":  item['Public IP'], "active":  item['Last active'], "download":  item['download'], "color": item['color'], "icon": item['icon']}

'''
save_file = open("output.json", "w")
json.dump(output, save_file)
save_file.close()'''
print(json.dumps(output, indent=4))