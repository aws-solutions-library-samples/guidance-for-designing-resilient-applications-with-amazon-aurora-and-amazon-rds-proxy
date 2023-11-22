# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import sys
sys.path.append('/opt')

import os
import json
import boto3
import psycopg2
import multi_region_db
from botocore.exceptions import ClientError as boto3_client_error

custom_functions = multi_region_db.Functions()
app_db_credentials = custom_functions.get_db_credentials('App')

def handler(event, context):
    
    print(json.dumps(event))
    
    env_data = {
        'clusterInfo': {}
    }
    
    rds_client = boto3.client('rds')
    sqs_client = boto3.client('sqs')
    
    ######################
    #### CLUSTER INFO ####
    ######################

    cluster_resp = rds_client.describe_db_clusters(
        DBClusterIdentifier = os.environ['APP_DB_CLUSTER_IDENTIFIER']
    )
        
    for member in cluster_resp['DBClusters'][0]['DBClusterMembers']:
        
        instance_resp = rds_client.describe_db_instances(
            DBInstanceIdentifier = member['DBInstanceIdentifier']
        )
        
        instance_data = {
            'az': instance_resp['DBInstances'][0]['AvailabilityZone'],
            'type': 'WRITER' if member['IsClusterWriter'] is True else 'READER'
        }
        
        try:
            
            db_conn = psycopg2.connect(
                host = instance_resp['DBInstances'][0]['Endpoint']['Address'],
                port = app_db_credentials['port'],
                user = app_db_credentials['username'],
                password = app_db_credentials['password'],
                database = app_db_credentials['database'],
                connect_timeout = 3,
                sslmode = 'require',
            )
            
            curs = db_conn.cursor()
            
            curs.execute('''
                SELECT
                    COUNT(*) AS count
                FROM dataserver
            ''');
            
            instance_records = curs.fetchone()
            
            instance_data['records'] = instance_records[0]
    
            curs.close()
            db_conn.close()
            
        except psycopg2.OperationalError as err:
            
            instance_data['records'] = 'N/A - Offline'
        
        env_data['clusterInfo'][member['DBInstanceIdentifier']] = instance_data
    
    ##############################
    #### QUEUE MESSAGE COUNTS ####
    ##############################
    
    try:
        
        pending_writes_queue_resp = sqs_client.get_queue_attributes(
            QueueUrl = os.environ['PENDING_WRITES_QUEUE_URL'],
            AttributeNames = [
                'ApproximateNumberOfMessages',
                'ApproximateNumberOfMessagesNotVisible',
            ]
        )
        
        attrs = pending_writes_queue_resp['Attributes']
        
        env_data['MessagesInPendingWritesQueue'] = int(attrs['ApproximateNumberOfMessages']) + int(attrs['ApproximateNumberOfMessagesNotVisible'])
        
        pending_writes_dl_queue_resp = sqs_client.get_queue_attributes(
            QueueUrl = os.environ['PENDING_WRITES_DL_QUEUE_URL'],
            AttributeNames = [
                'ApproximateNumberOfMessages',
                'ApproximateNumberOfMessagesNotVisible',
            ]
        )
        
        attrs = pending_writes_dl_queue_resp['Attributes']
        
        env_data['MessagesInPendingWritesDeadLetterQueue'] = int(attrs['ApproximateNumberOfMessages']) + int(attrs['ApproximateNumberOfMessagesNotVisible'])
        
    except boto3_client_error as e:
        raise Exception('Failed to Retrieve Queue Attributes: ' + str(e))
    
    return {
        'code': 200,
        'body': json.dumps(env_data)
    }