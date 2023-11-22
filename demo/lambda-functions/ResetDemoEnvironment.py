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

sqs_client = boto3.client('sqs')

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
        
        # nosemgrep - Not subject to user input (Semgrep)
        curs.execute('DELETE FROM ' + table_to_prune) # nosec - Not subject to user input (Bandit)
        
        db_conn.commit()
        
    curs.close()
    db_conn.close()
    
    return True
    
def purge_sqs_queue(queue_url):
    
    try:
        
        sqs_client.purge_queue(
            QueueUrl = queue_url,
        )
    
    except boto3_client_error as e:
        raise Exception('Failed to Purgue Queue: ' + str(e))
        
    return True

'''
    It is expected that this function will be run in the PRIMARY AWS region
'''
def handler(event, context):
    
    prune_db_tables('App', ['dataserver'])
    prune_db_tables('Demo', ['dataclient', 'failoverevents'])
    
    purge_sqs_queue(os.environ['PENDING_WRITES_QUEUE_URL'])
    purge_sqs_queue(os.environ['PENDING_WRITES_DL_QUEUE_URL'])
    
    return {
        'code': 200,
        'body': json.dumps([])
    }