# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import sys
import subprocess

subprocess.call('pip install urllib3<2 cfnresponse -t /tmp/ --no-cache-dir'.split(), stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL) # nosec Not subject to user input
sys.path.insert(1, '/tmp/') # nosec Required for module import

import io
import os
import json
import boto3
import cfnresponse
from botocore.exceptions import ClientError, ParamValidationError

'''
    - Region | str
    - ExportPrefix | str
'''
def handler(event, context):
    
    print(json.dumps(event))
    
    arguments = event['ResourceProperties']['Properties']
    operation = event['ResourceProperties']['Type'].replace('Custom::', '')
    
    response_data = {}
    
    boto3Session = boto3.Session(
        region_name = arguments['Region']
    )
    
    cfn_client = boto3Session.client('cloudformation')
    
    if event['RequestType'] in ['Create', 'Update']:
        
        try:
            
            response = cfn_client.list_exports()
            
            '''
                For each CloudFormation export in this region
            '''
            for export in response['Exports']:
            	
                '''
                    If this export has the proper prefix
                '''
                if export['Name'].startswith(arguments['ExportPrefix']):
                    
                    response_data[export['Name'].replace(arguments['ExportPrefix'] + '-', '')] = export['Value']
                
        except ClientError as e:
            
            print('Failed to Retrieve CFN Exports: ' + str(e.response))
            return cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
            
    return cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)