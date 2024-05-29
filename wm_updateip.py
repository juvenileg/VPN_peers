#! /bin/python
# Name: wm_updateip.py
# Author: gg
# Version 1.0
# Description: Script that checks DNS IP address and changes it if is not correct.

import requests
import socket
import datetime
import vard #my variable file
import subprocess

# Define API endpoints
base_url = 'https://api.cloudflare.com/client/v4/'

# Cloudflare authorization headers for DNS
headers = {
        "Content-Type": "application/json",
        "Authorization": vard.auth
    }

# Get current DNS record for the specified domain
def retrieve_dns(domain):
    params = {
        'name': {domain}
    }
    response = requests.request("GET", f'{base_url}zones/{vard.zone_identifier}/dns_records', headers=headers, params=params)
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
    requests.put(f'{base_url}zones/{vard.zone_identifier}/dns_records/{id}', json=data, headers=headers)

def connect(domain):
    command = "curl ipinfo.io/ip"
    srv_ip = subprocess.run(command, shell=True, capture_output=True)
    srv_ip = srv_ip.stdout.decode()
    my_text = 'Error'
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
        my_text = f"VPN Service down. Could not resolve {domain}, might be a problem with the script"
    return(my_text)

print(connect(vard.domain))