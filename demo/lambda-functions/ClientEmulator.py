# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import sys
sys.path.append('/opt')

import os
import json
import uuid
import psycopg2
import datetime
import dateutil.tz
import urllib.request
import multi_region_db
from botocore.vendored import requests

custom_functions = multi_region_db.Functions()
        
def handler(event, context):
    
    print(json.dumps(event))
    
    guid = uuid.uuid4()
    
    eastern = dateutil.tz.gettz('US/Eastern')

    demo_db_credentials = custom_functions.get_db_credentials('Demo')

    db_conn = psycopg2.connect(
        host = os.environ['DEMO_DB_CLUSTER_WRITER_ENDPOINT'],
        port = demo_db_credentials['port'],
        user = demo_db_credentials['username'],
        password = demo_db_credentials['password'],
        database = demo_db_credentials['database'],
        connect_timeout = 3,
        sslmode = 'require',
    )

    curs = db_conn.cursor()
    
    curs.execute('''
        INSERT INTO dataclient (guid, primary_region, failover_region, http_code, insertedon) 
            VALUES (%s, 0, 0, 0, %s)
    ''', (
        str(guid),
        datetime.datetime.now(tz = eastern).strftime("%m/%d/%Y %H:%M:%S")
    ))
    
    db_conn.commit()
    
    http_code = 200
    http_content = ''

    print('END guid: ' + str(guid))

    try:
        
        # nosemgrep - No subject to user input (Semgrep)
        res = urllib.request.urlopen(
            urllib.request.Request(
                url = 'https://' + os.environ['PUBLIC_APP_URL'] + '?guid=' + str(guid), # nosec - Not subject to user input (Bandit)
                method = 'GET',
            ),
            timeout = 5
        )
        
        http_code = res.status
        http_content = res.read().decode()
        
    except Exception as e:
        http_code = 500
        print('Client Web Request Failed :' + str(e))

    try: 

        if http_code > 200:
            http_content = ''
            
        print(http_code)
            
        curs = db_conn.cursor()
        
        curs.execute('''
            UPDATE dataclient SET
                http_code = %s
            WHERE guid = %s
        ''', (
            http_code,
            str(guid)
        ))
        
        db_conn.commit()
        
    except Exception as ex:
        http_code = 500
        print('Failed to Update Client Request: ' + str(ex) + ' - HTTP Content: "' + http_content + '"')
    
    curs.close()
    db_conn.close()
    
    return True