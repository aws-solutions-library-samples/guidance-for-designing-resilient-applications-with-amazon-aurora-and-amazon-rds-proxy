# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import sys
sys.path.append('/opt')

import os
import json
import psycopg2
import multi_region_db

custom_functions = multi_region_db.Functions()
        
def handler(event, context):
    
    print(json.dumps(event))
    
    db_conns = {}
    record_counts = {}
    app_db_credentials = custom_functions.get_db_credentials('App')
    
    for instance_number in ['1', '2']:
        
        try:
            
            db_conns[instance_number] = psycopg2.connect(
                host = os.environ['APP_DB_INSTANCE_' + instance_number + '_ENDPOINT'],
                port = app_db_credentials['port'],
                user = app_db_credentials['username'],
                password = app_db_credentials['password'],
                database = app_db_credentials['database'],
                connect_timeout = 3,
                sslmode = 'require',
            )
            
            curs = db_conns[instance_number].cursor()
            
            curs.execute('''
                SELECT
                    inet_server_addr() AS ip,
                    COUNT(*) AS count
                FROM dataserver
            ''');
            
            instance_data = curs.fetchone()
            
            record_counts[instance_number] = {
                'ip': instance_data[0],
                'records': instance_data[1]
            }
    
            curs.close()
            db_conns[instance_number].close()
            
        except psycopg2.OperationalError as err:
            
            record_counts[instance_number] = {
                'ip': 'N/A',
                'records': 'N/A - Offline'
            }
    
    return {
        'code': 200,
        'body': json.dumps(record_counts)
    }