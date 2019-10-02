import json
import os
import sys

import boto3
import botocore


comprehend_client = boto3.client('comprehend')

s3_resource = boto3.resource('s3')

ddb_client = boto3.client('dynamodb')

sentiment_table = os.getenv('SENTIMENT_TABLE')

def get_s3_object(bucket, key_name):
    try:
        s3_resource.Bucket(bucket).download_file(key_name, '/tmp/{}'.format(key_name))
        return 'ok'
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            return 'Error: s3://{}/{} does not exist'.format(bucket, key_name)
        else:
            return 'Error: {}'.format(str(e))

def put_sentiment(table_name, s3_object, sentiment):
    try:
        result = ddb_client.put_item(
            TableName=table_name,
            Item={
                'id': {
                    'S': s3_object
                },
                'sentiment': {
                    'S': sentiment['Sentiment']
                }
            }
        )
    except Exception as e:
        print('Error: {}'.format(str(e)))


def handler(event, context):
    for record in event['Records']:
        log_event = {}

        log_event['request_id'] = context.aws_request_id
        log_event['invoked_function_arn'] = context.invoked_function_arn
        log_event['sqs_message_id'] = record['messageId']
        log_event['sqs_event_source_arn'] = record['eventSourceARN']

        try:
            json_body = json.loads(record['body'])
            request_params = json_body['detail']['requestParameters']
            bucket_name = request_params['bucketName']
            key_name = request_params['key']
            log_event['source_s3_bucket_name'] = bucket_name
            log_event['source_s3_key_name'] = key_name

            download_status = get_s3_object(bucket_name, key_name)

            local_file = '/tmp/{}'.format(key_name)

            if download_status == 'ok':
                log_event['src_s3_download'] = 'ok'
                key_bytes = os.stat(local_file).st_size
                log_event['src_s3_download_bytes'] = key_bytes
            else:
                log_event['src_s3_download'] = download_status
                log_event['src_s3_download_bytes'] = -1
                sys.exit(1)
            
            md_contents = open(local_file, 'r').read()

            sentiment = comprehend_client.detect_sentiment(Text=md_contents, LanguageCode='en')

            log_event['sentiment'] = sentiment['Sentiment']
            log_event['sentiment_score'] = sentiment['SentimentScore']

            source_s3_object = 's3://{}/{}'.format(bucket_name, key_name)
            
            put_sentiment_result = put_sentiment(sentiment_table, source_s3_object, sentiment)

            print(put_sentiment_result)
        
        except Exception as e:
            log_event['error_msg'] = str(e)
            print(log_event)
            return 'fail'


        print(log_event)
        return('ok')

