#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import sys
import re
import json
import datetime

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <IP>\n")
    sys.exit(1)

HOST = sys.argv[1]
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 23
format = 'json'

# -------------------------------------------------------------------------

def get_sec(time_str: str) -> int:
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)

# -------------------------------------------------------------------------


try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error:
    print('Failed to create socket')
    sys.exit(1)

s.connect((HOST, PORT))

regex = r"^(\d+)\s+(\d{3})\s+(\d{3}\s+?)?([\d\:]+)\s+([\d\/]+ [\d:]+)\s+([A-Za-z0-9 :]+)\s+"

while True:
    try:
        line = s.recv(1024).decode()
        matches = re.findall(regex, line, re.MULTILINE | re.DOTALL)
        
        if ( (len(matches) > 0) and (len(matches[0]) >= 5) ):
            match = [s.strip() for s in matches[0]]
               
            id, phone, date, info = match[0], int(match[1]), match[4], match[5]
            date = datetime.datetime.strptime('28/04/21 17:02', '%d/%m/%y %H:%M').strftime('%Y-%m-%d %H:%M')
            co = match[2] or '000'
            co = int(co)
            duration = get_sec(match[3])
            
            if (format == 'json'):
                dumped = { 'pbx': HOST, 'event_id': id, 'date': date, 'co': co, 'phone': phone, 'duration': duration, 'info': info }
                print(json.dumps(dumped))
            else:
                print(f"{HOST} | {id} [{date}] {phone} / {co} @ {duration}\t({info})")
        
    except KeyboardInterrupt:
        s.close()
        sys.exit(0)
