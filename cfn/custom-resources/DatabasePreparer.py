# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import sys
sys.path.append('/opt')

import subprocess
subprocess.call('pip install urllib3<2 -t /tmp/ --no-cache-dir'.split(), stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL) # nosec Not subject to user input
sys.path.insert(1, '/tmp/') # nosec Required for package inclusion

import os
import json
import boto3
import psycopg2
import cfnresponse
import multi_region_db
from botocore.exceptions import ClientError as boto3_client_error

custom_functions = multi_region_db.Functions()

'''
    RDSAdminSecretArn
'''
def handler(event, context):
    
    print(json.dumps(event))
    
    if 'Properties' in event['ResourceProperties']:
        arguments = event['ResourceProperties']['Properties']
        
    operation = event['ResourceProperties']['Type'].replace('Custom::', '')
    
    response_data = {}
    
    if event['RequestType'] in ['Create', 'Update']:
        
        db_credentials = custom_functions.get_db_credentials(arguments['DatabaseIdentifier'])
        
        try:
                
            db_conn = psycopg2.connect(
                host = db_credentials['host'],
                port = db_credentials['port'],
                user = db_credentials['username'],
                password = db_credentials['password'],
                database = db_credentials['database'],
                connect_timeout = 3,
                sslmode = 'require',
            )
            
            curs = db_conn.cursor()
            
            for query in arguments['QueriesToExecute']:
                
                # nosemgrep - Not subject to user input
                curs.execute(query.replace('\r','').replace('\n',' '))
                db_conn.commit()
            
            curs.close()
            db_conn.close()
        
        except Exception as error:

            print('There was a problem executing the DDL statements: ' + str(error))
            return cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
            
    return cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)