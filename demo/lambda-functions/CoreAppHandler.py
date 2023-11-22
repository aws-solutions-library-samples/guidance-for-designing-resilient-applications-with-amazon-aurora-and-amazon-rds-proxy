# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import sys
sys.path.append('/opt')

import os
import json
import boto3
import datetime
import psycopg2
import dateutil.tz
import multi_region_db
from botocore.exceptions import ClientError as boto3_client_error

custom_functions = multi_region_db.Functions()

def handler(event, context):
    
    print(json.dumps(event))
    
    for incoming_record in event['Records']:
        
        guid = incoming_record['body']
        
        try:
            
            app_db_credentials = custom_functions.get_db_credentials('App')
            
            db_conn = psycopg2.connect(
                host = os.environ['APP_DB_PROXY_WRITER_ENDPOINT'],
                port = app_db_credentials['port'],
                user = app_db_credentials['username'],
                password = app_db_credentials['password'],
                database = app_db_credentials['database'],
                connect_timeout = 3,
                sslmode = 'require',
            )
            
            id = 0
            curs = db_conn.cursor()
            
            curs.execute('''
                INSERT INTO dataserver (guid, insertedon) VALUES (%s, %s) 
                RETURNING id
            ''', (
                guid,
                datetime.datetime.now(tz = dateutil.tz.gettz('US/Eastern')).strftime("%m/%d/%Y %H:%M:%S")
            ))
    
            id = curs.fetchone()[0]
            db_conn.commit()
            curs.close()
            db_conn.close()
        
        except Exception as e:
            print(e)
            raise Exception('Failed to Write Record to the Database')
    
    return True