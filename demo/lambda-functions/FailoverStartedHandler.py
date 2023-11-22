# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import sys
sys.path.append('/opt')

import os
import json
import boto3
import psycopg2
import datetime
import dateutil.tz
import multi_region_db
from botocore.exceptions import ClientError as boto3_client_error

custom_functions = multi_region_db.Functions()

def handler(event, context):
    
    print(json.dumps(event))
    
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
        INSERT INTO failoverevents (event, insertedon) 
            VALUES (2, %s)
    ''', (
        datetime.datetime.now(),
    ))
    
    db_conn.commit()
    
    curs.close()
    db_conn.close()
    
    return True