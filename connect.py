#! /bin/python
# Name: connect.py
# Author: gg
# Version 1.0
# Description: Script that tests IP address and nslookup and confirm status to HA for two VPN servers. Also checks if the IP address has changed with Cloudflare and updates the A record if it has.

import requests
import socket
import os
import datetime
import varc #my variable file

# Define API endpoints
base_url = 'https://api.cloudflare.com/client/v4/'

# Cloudflare authorization headers for DNS
headers = {
        "Content-Type": "application/json",
        "Authorization": varc.auth
    }

# Cloudflare authorization headers for tunnels
headers_tunnel = {
        "Content-Type": "application/json",
        "Authorization": varc.tunnel_auth
    }

# Get current DNS record for the specified domain
def retrieve_dns(domain):
    params = {
        'name': {domain}
    }
    response = requests.request("GET", f'{base_url}zones/{varc.zone_identifier}/dns_records', headers=headers, params=params)
    if response.status_code == 200:
        records = response.json()['result']
        if records:
            return records[0]['id'], records[0]['content']
    return '', ''

# Update the DNS record
def update_dns(id,new_ip_cf,domain):
    now = datetime.datetime.now()
    date_time_str = now.strftime("%d %b, %H:%M")
    data = {
        'content': new_ip_cf,
        'name': domain,
        'type': 'A',
        'proxied': False,
        'comment': f'Updated on {date_time_str} via automation'
    }
    requests.put(f'{base_url}zones/{varc.zone_identifier}/dns_records/{id}', json=data, headers=headers)

# Get tunnel status from Cloudflare
def retrieve_tunnel(domain):
    response = requests.request("GET", f'{base_url}accounts/{varc.acc_identifier}/tunnels', headers=headers_tunnel)
    records = {}
    if response.status_code == 200:
        records = response.json()['result']
    for key in records:
        if key['name'] == varc.tunnels[domain]:
            return key['status']
    return ''

def connect(srv,domain):
    srv_ip =''
    my_text ='VPN Service down.'
    srv_ip = os.popen(f'ssh {varc.user}@{srv} "curl ipinfo.io/ip"').read()
    if srv_ip == '':
        my_text = f'VPN Service down - Cloudflare tunnel is {retrieve_tunnel(domain)}'
    try:  
        addr = socket.gethostbyname(domain)
        if addr == srv_ip:
            my_text = f"VPN Service OK - IP address of {domain} is {addr}, as expected."
        elif srv_ip != '':
            my_text = f"VPN Service down - IP address of {domain} is {addr}. Expected IP is {srv_ip}, Attempted Cloudflare DNS update, waiting..."
            id, new_ip = retrieve_dns(domain) #if clouflare DNS entry not matches the ip address on the server, update Cloudflare entry
            if new_ip != srv_ip:
                update_dns(id,srv_ip,domain)
            else:
                my_text = f"VPN Service down. IP address of {domain} is {addr}. Expected IP is {srv_ip}. Cloudflare DNS changed with success."
    except socket.gaierror:
        my_text = f"VPN Service down. Could not resolve {domain}, might be a problem with the script, but I can connect through Cloudflare tunnel"
    return(my_text)

#print(my_text)
now = datetime.datetime.now()
date_time_str = now.strftime("%d %b, %H:%M")
with open('connect.txt', 'w') as f:
    f.write(f'{date_time_str} : {connect(varc.srv1,varc.domain)}')
with open('connect1.txt', 'w') as f:
    f.write(f'{date_time_str} : {connect(varc.srv3,varc.domain1)}')

# Rsync file to another server
os.system(f'rsync -avz connect.txt connect1.txt -e "ssh -i /home/ubuntu/.ssh/id_ed25519" {varc.user}@{varc.srv2}:/home/{varc.user}/Drive/conf_files/homeassistant/scripts')
