import json
import logging
import os

import boto3
import cfnresponse


aws_region = os.environ['AWS_REGION']

s3_client = boto3.client('s3', region_name=aws_region)
sqs_client = boto3.client('sqs', region_name=aws_region)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def addBucketNotification(bucket_name, notification_id, sns_arn, sqs_urls):
    notificationResponse = s3_client.put_bucket_notification_configuration(
        Bucket=bucket_name,
        NotificationConfiguration={
            'TopicConfigurations': [
                {
                    'Id': notification_id,
                    'TopicArn': sns_arn,
                    'Events': [
                        's3:ObjectCreated:*'
                    ]
                },
            ]
        }
    )

    # Purge the SQS Queues once notification configuration has been set.
    # This will avoid the issue of s3:Test messages being consumed by 
    # the Conversion and Sentiment Lambda functions.
    for sqs_url in sqs_urls:
        logger.info(f'Clearing queue {sqs_url}')
        purgeResponse = sqs_client.purge_queue(QueueUrl=sqs_url)
        logger.info(f'PurgeQueue response: {json.dumps(purgeResponse)}')

    return notificationResponse

def create(properties, physical_id):
    bucket_name = properties['S3Bucket']
    notification_id = properties['NotificationId']
    sns_arn = properties['SnsArn']
    sqs_urls = properties['SqsUrls']
    response = addBucketNotification(bucket_name, notification_id, sns_arn, sqs_urls)
    logger.info(f'AddBucketNotification response: {json.dumps(response)}')
    return cfnresponse.SUCCESS, physical_id

def update(properties, physical_id):
    return cfnresponse.SUCCESS, None

def delete(properties, physical_id):
    return cfnresponse.SUCCESS, None

def handler(event, context):
    logger.info(f'Received event: {json.dumps(event)}')

    status = cfnresponse.FAILED
    new_physical_id = None

    try:
        properties = event.get('ResourceProperties')
        physical_id = event.get('PhysicalResourceId')

        status, new_physical_id = {
            'Create': create,
            'Update': update,
            'Delete': delete
        }.get(event['RequestType'], lambda x, y: (cfnresponse.FAILED, None))(properties, physical_id)
    except Exception as e:
        logger.error('Exception: %s' % e)
        status = cfnresponse.FAILED
    finally:
        cfnresponse.send(event, context, status, {}, new_physical_id)
