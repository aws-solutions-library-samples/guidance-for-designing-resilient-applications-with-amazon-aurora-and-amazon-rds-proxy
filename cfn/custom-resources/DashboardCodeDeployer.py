# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import sys
import subprocess

subprocess.call('pip install urllib3<2 cfnresponse -t /tmp/ --no-cache-dir'.split(), stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL) # nosec Not subject to user input
sys.path.insert(1, '/tmp/') # nosec Required for modeul import

import os
import json
import glob
import boto3
import shutil
import urllib3
import zipfile
import mimetypes
import cfnresponse
from collections import defaultdict
from botocore.exceptions import ClientError as boto3_client_error

http = urllib3.PoolManager()

try:
    from urllib2 import HTTPError, build_opener, HTTPHandler, Request
except ImportError:
    from urllib.error import HTTPError
    from urllib.request import build_opener, HTTPHandler, Request
    
'''
    - CodeBucketName | str
    - CodeDownloadUrl | str
    - DemoAppApiKeyId | str
'''
def handler(event, context):
    
    print(json.dumps(event))
    
    arguments = event['ResourceProperties']['Properties']
    
    s3_client = boto3.client('s3')
    
    response_data = {}
    
    if event['RequestType'] in ['Create', 'Update']:
        
        path_to_local_zip = '/tmp/demo_ui_code.zip' # nosec Required to download dashboard code
        path_to_local_dir = path_to_local_zip.replace('.zip', '')
        
        '''
            Download the codebase
        '''
        http = urllib3.PoolManager()
        code_download_response = http.request('GET', arguments['CodeDownloadUrl'], preload_content = False, headers = {
            'Cookie': '_gh_sess={}; user_session={}'.format(os.environ['GITHUB_GH_SESSION_COOKIE'], os.environ['GITHUB_USER_SESSION_COOKIE'])
        })
        
        if code_download_response.status != 200:
            print('Failed to Download Demo UI Code: HTTP Code ' + str(code_download_response.status))
            return cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
			
        with code_download_response as r, open(path_to_local_zip, 'wb') as out_file:
            shutil.copyfileobj(r, out_file)
        
        '''
            Unzip the downloaded code
        '''
        with zipfile.ZipFile(path_to_local_zip, 'r') as zip_ref:
            zip_ref.extractall(path_to_local_dir)
            
        dashboard_ui_path = '/demo/dashboard-ui/'
        
        try:
            
            demo_api_key_resp = boto3.client('apigateway').get_api_key(
                apiKey = arguments['DemoAppApiKeyId'],
                includeValue = True
            )
            
            demo_api_key_value = demo_api_key_resp['value']
            
        except boto3_client_error as e:
            print('Failed to Retrieve API Key: ' + str(e))
            return cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
            
        '''
            For each file in the local code directory
        '''
        for file_path in glob.iglob(path_to_local_dir + '**/**', recursive = True):
            
            '''
                If it's one of the dashboard files and it's a file, not a directory, we'll upload it to S3
            '''
            if dashboard_ui_path in file_path and os.path.isfile(file_path):
                
                '''
                    If it's the index file, we need to add the API key to authenticate Demo API requests.
                '''
                if file_path[-10:] == 'index.html':

                    with open(file_path, 'r') as file:
                        file_contents = file.read()

                    file_contents = file_contents.replace('{{DEMO-API-KEY}}', demo_api_key_value)

                    with open(file_path, 'w') as file:
                        file.write(file_contents)

                    print('Added API Key to Demo UI Index File: ' + file_path)
            
                try:
                    
                    s3_key = file_path.split(dashboard_ui_path)[1]
                    
                    s3_client.upload_file(file_path, arguments['CodeBucketName'], s3_key,
                        ExtraArgs = {
                            'ContentType': mimetypes.guess_type(file_path)[0]
                        })
                    
                except boto3_client_error as e:
                    print('Failed to Upload Dashboard File: ' + str(e))
                    return cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        
    elif event['RequestType'] in ['Delete']:
        
        return cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)
        
        '''
            Here, we'll delete all objects, versions, and delete markers from the bucket.
        '''
        object_response_paginator = s3_client.get_paginator('list_object_versions')
        
        objects_to_delete = []
        
        for object_response_iterator in object_response_paginator.paginate(Bucket = arguments['CodeBucketName']):
            
            for object_group in ['Versions', 'DeleteMarkers']:
                
                if object_group in object_response_iterator:
                
                    for object_data in object_response_iterator[object_group]:
                    
                        objects_to_delete.append({
                            'Key': object_data['Key'], 
                            'VersionId': object_data['VersionId']
                        })
                    
        for i in range(0, len(objects_to_delete), 1000):
            
            try:
                
                response = s3_client.delete_objects(
                    Bucket = arguments['CodeBucketName'],
                    Delete = {
                        'Objects': objects_to_delete[i:i + 1000],
                        'Quiet': True
                    }
                )
                
            except boto3_client_error as e:
                print('Failed to Delete S3 Objects: ' + str(e))
                return cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
        
    return cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)