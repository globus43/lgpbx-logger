#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import sys
import re
import json
import datetime
import mysql.connector
import time


HOST = sys.argv[1]
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 23
format = 'json'
sql = True

MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'pass4sql'
MYSQL_DATABASE = 'pbx_logs'

# -------------------------------------------------------------------------
def get_sec(time_str: str) -> int:
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)

# -------------------------------------------------------------------------
def do_work():
    DATE_FORMAT = '%d/%m/%y %H:%M'
    sql = True
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        
        s.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 60)
        s.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 4)
        s.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 15)
        
        s.settimeout(120.0)
        s.connect((HOST, PORT))
    except socket.error:
        print('Failed to create socket')
        sys.exit(1)

    if sql:
        print('SQL connect')
        while True:
            try:
                sql = mysql.connector.connect(
                    host = MYSQL_HOST,
                    user = MYSQL_USER,
                    passwd = MYSQL_PASSWORD,
                    database = MYSQL_DATABASE,
                    charset = "utf8"
                )
                break
            except ConnectionRefusedError:
                print('Connection refused. Reconnecting...')
                time.sleep(10)
                continue
        mycursor = None

    regex = r"^(\d+)\s+(\d{3})\s+(\d{3}\s+?)?([\d\:]+)\s+([\d\/]+ [\d:]+)\s+([A-Za-z0-9 :]+)\s+"

    while True:
        try:
            line = s.recv(1024).decode()
        
            matches = re.findall(regex, line, re.MULTILINE | re.DOTALL)
        
            if ( (len(matches) > 0) and (len(matches[0]) >= 5) ):
                match = [s.strip() for s in matches[0]]
               
                id, phone, date, info = match[0], int(match[1]), match[4], match[5]

                if date.split(sep = '/', maxsplit = 2)[0] == datetime.date.today().strftime('%m'):
                    DATE_FORMAT = '%m/%d/%y %H:%M'
                date = datetime.datetime.strptime(date, DATE_FORMAT).strftime('%Y-%m-%d %H:%M')

                co = match[2] or '000'
                co = int(co)
                duration = get_sec(match[3])
            
                if sql:
                    for attempt in range(5):
                        try:
                            mycursor = sql.cursor()
                            query = "INSERT INTO `logs` (`pbx`, `event_id`, `date`, `co`, `phone`, `duration`, `info`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                            vals = (HOST, id, date, co, phone, duration , info)
                            mycursor.execute(query, vals)
                            sql.commit()
                        except (mysql.connector.Error, mysql.connector.errors.OperationalError) as e:
                            print('SQL reconnect...')
                            sql.reconnect()
                        else:
                            break
            
                if (format == 'json'):
                    dumped = { 'pbx': HOST, 'event_id': id, 'date': date, 'co': co, 'phone': phone, 'duration': duration, 'info': info }
                    print(json.dumps(dumped))
                else:
                    print(f"{HOST} | {id} [{date}] {phone} / {co} @ {duration}\t({info})")
        
        except KeyboardInterrupt:
            if sql:
                if mycursor:
                    mycursor.close()
                sql.close()
            s.close()
            sys.exit(0)
            
        except socket.timeout:
            #print('Timeout...')
            continue
        except ConnectionResetError:
            print('Connection reset')
            continue
            
    try:
        s.close()
    except:
        pass

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <IP>\n")
        sys.exit(1)

    do_work()
