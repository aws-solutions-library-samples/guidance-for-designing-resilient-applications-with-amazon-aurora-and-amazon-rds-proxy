# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import time
import json
import boto3

def handler(event, context):
    
    print(json.dumps(event))

    sns_client = boto3.client('sns')
    
    for i in range(0, 3000):
        
        sns_client.publish(
            Message = 'Hola',
            TargetArn = os.environ['TEST_TRAFFIC_TOPIC_ARN'],
        )
        
        time.sleep(0.05)
    
    return {
        'code': 200,
        'body': json.dumps([])
    }
