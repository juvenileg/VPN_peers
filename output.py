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

match1 = re.findall(r'endpoint:.(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', output1)
match2 = re.findall(r'ips:.(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', output1)
match3 = re.findall(r'handshake:.(.*)', output1)
match4 = re.findall(r'transfer:.(.*)\s*.received', output1)
match5 = re.findall(r'received,.(.*)\s*.sent', output1)

files = os.listdir(varo.path)
for file in files:
    if file.startswith('peer'):
        nfile = file[5:]
        vpn = {'Peer' : nfile}
        command = f'cat {varo.path}/{file}/{file}.conf | grep Address'
        output = subprocess.run(command, shell=True, capture_output=True)
        output = output.stdout.decode()
        match = re.search(r'\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}', output)
        for i in range(len(match1)):
            if match.group() == match2[i]:
                vpn.update({'Public IP' : match1[i],'Private IP' : match2[i],'Last active' : match3[i],'upload' : match4[i],'download' : match5[i]})
                vpns.append(vpn)

print(json.dumps(vpns, indent=4))