# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import sys
sys.path.append('/opt')

import os
import json
import boto3
import psycopg2
import dateutil.tz
import multi_region_db
from datetime import datetime
from botocore.exceptions import ClientError as boto3_client_error

custom_functions = multi_region_db.Functions()

def prune_db_tables(db_identifier, table_names):
    
    db_credentials = custom_functions.get_db_credentials(db_identifier)
    
    db_conn = psycopg2.connect(
        host = os.environ[db_identifier.upper() + '_DB_CLUSTER_WRITER_ENDPOINT'],
        port = db_credentials['port'],
        user = db_credentials['username'],
        sslmode = 'require',
        password = db_credentials['password'],
        database = db_credentials['database'],
        connect_timeout = 3,
    )
    
    for table_to_prune in table_names:
        
        curs = db_conn.cursor()
        curs.execute('DELETE FROM ' + table_to_prune)
        db_conn.commit()
        
    curs.close()
    db_conn.close()
    
    return True

'''
    It is expected that this function will be run in the PRIMARY AWS region
'''
def handler(event, context):
    
    prune_db_tables('App', ['dataserver'])
    prune_db_tables('Demo', ['dataclient', 'failoverevents'])
    
    return {
        'code': 200,
        'body': json.dumps([])
    }