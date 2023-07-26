#! /bin/python
# Name: connect.py
# Author: gg
# Version 1.0
# Description: Script that tests IP address and nslookup and confirm status to HA

import socket
import os
import datetime
import varc #my variable file

srv_ip =''
my_text ='Server is down'


try:
    srv_ip = os.popen(f'ssh {varc.user}@{varc.srv1} "curl ipinfo.io/ip"').read()
except:
    my_text = "Cannot connect via Cloudflare, Server could be down"

try:  
    addr = socket.gethostbyname(varc.domain)
    if addr == srv_ip:
        my_text = f"IP address of {varc.domain} is {addr}. It matches the expected IP address. Your server should be OK for VPN connections"
    else:
        my_text = f"IP address of {varc.domain} is {addr}. It does not match the expected IP {srv_ip}, RDS address might have changed and VPN is down!"
except socket.gaierror:
    my_text = f"Could not resolve {varc.domain}, might be a problem with the script, but I can connect through Cloudflare tunnel"

#print(my_text)
now = datetime.datetime.now()
date_time_str = now.strftime("%d %b, %H:%M")
with open('connect.txt', 'w') as f:
    f.write(f'{date_time_str} : {my_text}')

# Rsync file to another server
os.system(f'rsync -avz connect.txt -e "ssh -i /home/ubuntu/.ssh/id_ed25519" {varc.user}@{varc.srv2}:/home/{varc.user}/Drive/conf_files/homeassistant/scripts/connect.txt')
