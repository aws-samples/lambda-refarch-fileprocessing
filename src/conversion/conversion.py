import json
import logging
import os
import sys

import aws_lambda_logging
import boto3
import botocore
import markdown
import tempfile


max_object_size = 104857600  # 100MB = 104857600 bytes

conversion_queue = os.getenv('CONVERSION_QUEUE')

target_bucket = os.getenv('TARGET_BUCKET')

log_level = os.getenv('LOG_LEVEL')

s3_resource = boto3.resource('s3')

sqs_client = boto3.client('sqs')

log = logging.getLogger()


def check_s3_object_size(bucket, key_name):
    try:
        size = s3_resource.Object(bucket, key_name).content_length
    except Exception as e:
        log.error(f'Error: {str(e)}')
        size = 'NaN'

    return(size)


def get_s3_object(bucket, key_name, local_file):
    try:
        s3_resource.Bucket(bucket).download_file(key_name, local_file)
        return('ok')
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            return(f'Error: s3://{bucket}/{key_name} does not exist')
        else:
            return(f'Error: {str(e)}')


def convert_to_html(file):
    try:
        file_open = open(file, 'r')
        file_string = file_open.read()
        file_open.close()

    except Exception as e:
        log.error(f'Could not open or read {file}: {str(e)}')
        raise

    return(markdown.markdown(file_string))


def upload_html(target_bucket, target_key, source_file):
    try:
        s3_resource.Object(target_bucket, target_key).upload_file(source_file)
        html_upload = 'ok'
    except Exception as e:
        log.error(f'Could not upload {source_file} to {target_bucket}: {str(e)}')
        html_upload = 'fail'

    return(html_upload)


def handler(event, context):
    aws_lambda_logging.setup(level=log_level,
                             aws_request_id=context.aws_request_id)

    for record in event['Records']:
        tmpdir = tempfile.mkdtemp()

        sqs_message_id = record['messageId']
        sqs_event_source_arn = record['eventSourceARN']

        sqs_receipt_handle = record['receiptHandle']

        try:
            json_body = json.loads(record['body'])
            request_params = json_body['detail']['requestParameters']
            bucket_name = request_params['bucketName']
            key_name = request_params['key']

            size = check_s3_object_size(bucket_name, key_name)

            if size >= max_object_size:
                log.error(f'''Source S3 object s3://{bucket_name}/{key_name} is larger ({size} bytes)
                than {max_object_size} (max object bytes)''')
                raise Exception('Source S3 object too large')

            local_file = os.path.join(tmpdir, key_name)

            download_status = get_s3_object(bucket_name, key_name, local_file)

            if download_status == 'ok':
                key_bytes = os.stat(local_file).st_size
                log.info(f'Success: Download to {local_file} for conversion')
            else:
                log.error(f'Fail to put object to {local_file}')
                raise Exception(f'Fail to put object to {local_file}')

            html = convert_to_html(local_file)

            html_filename = os.path.splitext(key_name)[0] + '.html'

            local_html_file = os.path.join(tmpdir, html_filename)

            with open(local_html_file, 'w') as outfile:
                outfile.write(html)
                log.info(f'''Success: Converted s3://{bucket_name}/{key_name}
                 to {local_html_file}''')
            outfile.close()

            html_upload = upload_html(target_bucket,
                                      html_filename,
                                      local_html_file)
            if html_upload == 'ok':
                '''If function could put the converted file to the S3 bucket then
                remove message from the SQS queue'''
                try:
                    sqs_client.delete_message(
                        QueueUrl=conversion_queue,
                        ReceiptHandle=sqs_receipt_handle
                    )
                except Exception as e:
                    log.error(f'{str(e)}')
                    raise Exception(str(e))
                dst_s3_object = f's3://{target_bucket}/{html_filename}'
                log.info(f'''Success: Uploaded {local_html_file} to
                 {dst_s3_object}''')
            else:
                log.error(f'{str(e)}')
                raise Exception(f'{str(e)}')

        except Exception as e:
            log.error(f'Could not convert record: {str(e)}')
            raise Exception(f'Could not convert record: {str(e)}')

        finally:
            filesToRemove = os.listdir(tmpdir)

            for f in filesToRemove:
                file_path = os.path.join(tmpdir, f)
                log.info(f'Removing File: {file_path}')

                try:
                    os.remove(file_path)
                except OSError as e:
                    log.error(f'Could not delete file {file_path}: {str(e)}')

            log.info(f'Removing Folder: {tmpdir}')
            os.rmdir(tmpdir)

        return('ok')
