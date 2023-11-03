# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import sys
sys.path.append('/opt')

import os
import json
import psycopg2	
import dateutil.tz
import multi_region_db
from datetime import datetime	
from datetime import timedelta

custom_functions = multi_region_db.Functions()

def handler(event, context):
    
    print(json.dumps(event))
    
    demo_db_credentials = custom_functions.get_db_credentials('Demo')
    
    db_conn = psycopg2.connect(
        host = os.environ['DEMO_DB_CLUSTER_WRITER_ENDPOINT'],
        port = demo_db_credentials['port'],
        user = demo_db_credentials['username'],
        sslmode = 'require',
        password = demo_db_credentials['password'],
        database = demo_db_credentials['database'],
        connect_timeout = 3,
    )
    
    curs = db_conn.cursor()	
    
    curs.execute('''
        SELECT
            insertedon,
            sum(CASE WHEN http_code = 200 THEN 1 ELSE 0 END)
        FROM dataclient
        WHERE http_code != 0
        GROUP BY insertedon
        ORDER BY insertedon DESC 
        LIMIT 15
    ''')
    
    traffic_records = curs.fetchall()
    
    curs.close()	
    db_conn.close()
    
    data_arr = []	
    label_arr = []
    
    '''
        For each traffic record found
    '''
    for record in reversed(traffic_records):
        
        data_arr.append(str(record[1]))
        label_arr.append(str(record[0]))
    
    if len(label_arr) > 0:
        
        for n in range(len(label_arr) + 1, 16):	
            
            data_arr.insert(0, '0')
            label_arr.insert(0, custom_functions.subtract_five_seconds(label_arr[0]))
    
    #custom_functions.add_time(label_arr, data_arr)
        
    return {
        'code': 200,
        'body': json.dumps([{
            'data': ','.join(data_arr),
            'labels': ','.join(label_arr),
        }])
    }