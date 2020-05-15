from datetime import datetime
import json
import logging
import os
import sys
import tempfile

import aws_lambda_logging
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
import boto3
import botocore

patch_all()


max_object_size = 104857600  # 100MB = 104857600 bytes

aws_region = os.environ['AWS_REGION']

s_table = os.getenv('SENTIMENT_TABLE')
s_queue = os.getenv('SENTIMENT_QUEUE')

log_level = os.getenv('LOG_LEVEL')

comprehend_client = boto3.client('comprehend', region_name=aws_region)

s3_resource = boto3.resource('s3', region_name=aws_region)

dynamodb_resource = boto3.resource('dynamodb', region_name=aws_region)
table = dynamodb_resource.Table(s_table)

sqs_client = boto3.client('sqs', region_name=aws_region)

log = logging.getLogger()


def check_s3_object_size(bucket, key_name):
    """Take in a bucket and key and return the number of bytes

    Parameters
    ----------
    bucket: string, required
        Bucket name where object is stored

    key_name: string, required
        Key name of object

    Returns
    -------
    size: integer
        Size of key_name in bucket
    """

    xray_recorder.begin_subsegment('## get_object_size')
    subsegment = xray_recorder.current_subsegment()
    subsegment.put_metadata('object', f's3://{bucket}/{key_name}')

    try:
        size = s3_resource.Object(bucket, key_name).content_length
        subsegment.put_metadata('object_size', size)
    except Exception as e:
        log.error(f'Error: {str(e)}')
        size = 'NaN'
        subsegment.put_metadata('object_size', size)

    xray_recorder.end_subsegment()
    return(size)


def get_s3_object(bucket, key_name, local_file):
    """Download object in S3 to local file

    Parameters
    ----------
    bucket: string, required
        Bucket name where object is stored

    key_name: string, required
        Key name of object

    local_file: string, required

    Returns
    -------
    result: string
        Result of operation ('ok' or exception)
    """

    xray_recorder.begin_subsegment('## get_object_to_analyze')
    subsegment = xray_recorder.current_subsegment()
    subsegment.put_metadata('object', f's3://{bucket}/{key_name}')

    try:
        s3_resource.Bucket(bucket).download_file(key_name, local_file)
        result = 'ok'
        subsegment.put_annotation('OBJECT_DOWNLOAD', 'SUCCESS')
    except botocore.exceptions.ClientError as e:
        subsegment.put_annotation('OBJECT_DOWNLOAD', 'FAILURE')
        if e.response['Error']['Code'] == '404':
            result = f'Error: s3://{bucket}/{key_name} does not exist'
        else:
            result = f'Error: {str(e)}'

    xray_recorder.end_subsegment()
    return(result)


def put_sentiment(s3_object, sentiment):
    """Put the sentiment of a object to DynamoDB

    Parameters
    ----------
    s3_object: string, required
        Location of the S3 object to analyze

    sentiment: dict, required
        Sentiment dictionary from Comprehend

    Returns
    -------
    result: string
        Result of operation ('ok' or exception)
    """

    xray_recorder.begin_subsegment('## put_sentiment_to_db')
    subsegment = xray_recorder.current_subsegment()

    try:
        response = table.put_item(
            Item={
                'id': s3_object,
                'last_modified': datetime.utcnow().isoformat(),
                'overall_sentiment': sentiment['Sentiment'],
                'positive': str(sentiment['SentimentScore']['Positive']),
                'negative': str(sentiment['SentimentScore']['Negative']),
                'neutral': str(sentiment['SentimentScore']['Neutral']),
                'mixed': str(sentiment['SentimentScore']['Mixed'])
            }
        )

        result = 'ok'
        subsegment.put_annotation('PUT_SENTIMENT_TO_DB', 'SUCCESS')
    except Exception as e:
        result = str(e)
        subsegment.put_annotation('PUT_SENTIMENT_TO_DB', 'FAILURE')
        result = f'Error: {str(e)}'
        log.error(response)

    xray_recorder.end_subsegment()
    return(result)


def handler(event, context):
    aws_lambda_logging.setup(level=log_level,
                             aws_request_id=context.aws_request_id)

    for record in event['Records']:
        tmpdir = tempfile.mkdtemp()

        sqs_receipt_handle = record['receiptHandle']

        try:
            json_body = json.loads(record['body'])

            for record in json_body['Records']:
                bucket_name = record['s3']['bucket']['name']
                key_name = record['s3']['object']['key']

                size = check_s3_object_size(bucket_name, key_name)

                if size >= max_object_size:
                    error_message = f'Source S3 object '
                    error_message += f's3://{bucket_name}/{key_name} '
                    error_message += f'is larger '
                    error_message += f'than {max_object_size} '
                    error_message += f'(max object bytes)'
                    log.error(error_message)
                    raise Exception(error_message)

                if size == 'NaN':
                    exc = f'Could not get size for '
                    exc += f's3://{bucket_name}/{key_name}'
                    raise Exception(exc)

                local_file = os.path.join(tmpdir, key_name)

                download_status = get_s3_object(bucket_name,
                                                key_name,
                                                local_file)

                if download_status == 'ok':
                    success_message = f'Download to {local_file} '
                    success_message += f'for sentiment analysis'
                    log.info(success_message)
                else:
                    log.error(f'Download failure to {local_file}')
                    raise Exception(f'Download failure to {local_file}')

                md_contents = open(local_file, 'r').read()

                sentiment = comprehend_client.detect_sentiment(
                    Text=md_contents,
                    LanguageCode='en'
                )

                overall_sentiment = sentiment['Sentiment']
                sentiment_score = sentiment['SentimentScore']

                sentiment_message = f'{overall_sentiment} ({sentiment_score})'
                log.info(sentiment_message)

                source_s3_object = f's3://{bucket_name}/{key_name}'

                put_sentiment_result = put_sentiment(source_s3_object,
                                                     sentiment)

                if put_sentiment_result == 'ok':
                    '''If function could put the sentiment to the DDB table then
                    remove message from SQS queue.'''
                    try:
                        sqs_client.delete_message(
                            QueueUrl=s_queue,
                            ReceiptHandle=sqs_receipt_handle
                        )
                    except Exception as e:
                        err_msg = f'Could not remove message '
                        err_msg += f'from queue: {str(e)}'
                        log.error(err_msg)
                        raise Exception(err_msg)

                    sentiment_db_msg = f'Put sentiment to {s_table}'
                    log.info(sentiment_db_msg)
                else:
                    db_put_error_msg = f'Could not put sentiment '
                    db_put_error_msg += f'to {s_table}: '
                    db_put_error_msg += f'{put_sentiment_result}'
                    log.error(db_put_error_msg)
                    raise Exception(db_put_error_msg)
        except Exception as e:
            log.error(f'Could not get sentiment: {str(e)}')
            raise Exception(f'Could not get sentiment: {str(e)}')
        finally:
            filesToRemove = os.listdir(tmpdir)

            for f in filesToRemove:
                file_path = os.path.join(tmpdir, f)
                log.debug(f'Removing File: {file_path}')

                try:
                    os.remove(file_path)
                except OSError as e:
                    log.error(f'Could not delete file {file_path}: {str(e)}')

            log.debug(f'Removing Folder: {tmpdir}')
            os.rmdir(tmpdir)

    return('ok')
