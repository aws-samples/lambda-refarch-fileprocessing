import boto3
import logging
import json
import cfnresponse

s3Client = boto3.client('s3')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def addBucketNotification(bucket_name, notification_id, sns_arn):
    notificationResponse = s3Client.put_bucket_notification_configuration(
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
    return notificationResponse

def create(properties, physical_id):
    bucket_name = properties['S3Bucket']
    notification_id = properties['NotificationId']
    sns_arn = properties['SnsArn']
    response = addBucketNotification(bucket_name, notification_id, sns_arn)
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
