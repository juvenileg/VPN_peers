#! /bin/python
# Name: peers.py
# Author: gg
# Version 1.0
# Description: Script that connects to two servers, retrieves the json vpn details, queries for resolving city and org for each ip address
# and then uploads the json result to home assistant

import os
import json
import ipinfo
import varp # my variable file
import re

handler = ipinfo.getHandler(varp.token)

def ip_in_json(ip_address): #Function that determines the city, contry and org if not saved in ip_file.json
    with open('ip_file.json', "r") as f:
        data = json.load(f)
        f.close()
        if ip_address in data:
            return data[ip_address]['city'], data[ip_address]['org']
        else:
            try:
                details = handler.getDetails(ip_address)
                data[ip_address] = {"city": details.city,"country": details.country,"org": details.org}
                with open('ip_file.json', "w") as f:
                    json.dump(data, f, indent=4)
                    f.close()
            except:
                return 'N/A','N/A'

def get_json(srv):
    try:
        output = os.popen(f'ssh {varp.user}@{srv} "python3 output.py"').read()
        data = json.loads(output)
    except:
        data = { 'd1' : 'error'}
    return(data)

def new_json(data,ind):
    output ={}
    i = 0
    for item in data:
        minutes = 0
        i += 1
        for var in re.findall(r'(\d+) day', item['Last active']): #extract minutes to show only peers active in the last 30 mins.
            minutes += int(var) * 60
        for var in re.findall(r'(\d+) hour', item['Last active']): #extract minutes to show only peers active in the last 30 mins.
            minutes += int(var) * 60
        for var in re.findall(r'(\d+) minutes', item['Last active']):
            minutes += int(var)
        if minutes < 31:
            color ="green"
            icon = "mdi:lan-connect"
        else:
            color ="#a60b00"
            icon = "mdi:lan-disconnect"
        output[ind+str(i)] = {"peer": item['Peer'], "ip":  item['Public IP'], "active":  item['Last active'], "download":  item['download'], "color": color, "icon": icon}
    return(output)


#print(json.dumps(new_json(get_json(varp.srv2),'d'), indent=4))

data1 = new_json(get_json(varp.srv2),'d')
data2 = new_json(get_json(varp.srv1),'e')
data3 = {**data1, **data2}

#print(ip_in_json("8.8.8.8")) #for testing purposes

for key in data3: #re-writes the json data with city and org details
    key1= ip_in_json(data3[key]['ip'])
    data3[key]['city'] = key1[0]
    data3[key]['org'] = key1[1]

#print(json.dumps(data3, indent=4)) #for testing purposes

save_file = open("wire.json", "w")
json.dump(data3, save_file, indent=4)
save_file.close()

# Rsync file to another server
os.system(f'rsync -avz wire.json -e "ssh -i /home/ubuntu/.ssh/id_ed25519" {varp.user}@{varp.srv2}:/home/{varp.user}/Drive/conf_files/homeassistant/scripts/wire.json')