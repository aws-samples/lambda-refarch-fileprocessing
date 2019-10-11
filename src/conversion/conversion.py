import json
import os
import sys

import boto3
import botocore
import markdown
import tempfile

max_object_size = 104857600  # 100MB = 104857600 bytes

target_bucket = os.getenv('TARGET_BUCKET')

s3_resource = boto3.resource('s3')


def check_s3_object_size(bucket, key_name):
    try:
        size = s3_resource.Object(bucket, key_name).content_length
    except Exception as e:
        print('Error: {}'.format(str(e)))
        size = 'NaN'

    return size


def get_s3_object(bucket, key_name, local_file):
    try:
        s3_resource.Bucket(bucket).download_file(key_name, local_file)
        return 'ok'
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            return 'Error: s3://{}/{} does not exist'.format(bucket, key_name)
        else:
            return 'Error: {}'.format(str(e))


def convert_to_html(file):
    try:
        file_open = open(file, 'r')
        file_string = file_open.read()
        file_open.close()

    except Exception as e:
        print('Error: {}'.format(str(e)))
        raise

    return markdown.markdown(file_string)


def upload_html(target_bucket, target_key, source_file):
    try:
        s3_resource.Object(target_bucket, target_key).upload_file(source_file)
        html_upload = 'ok'
    except Exception as e:
        print('Error: {}'.format(str(e)))
        html_upload = 'fail'

    return html_upload


def handler(event, context):
    for record in event['Records']:
        tmpdir = tempfile.mkdtemp()

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

            size = check_s3_object_size(bucket_name, key_name)

            local_file = os.path.join(tmpdir, key_name)

            download_status = get_s3_object(bucket_name, key_name, local_file)

            if download_status == 'ok':
                log_event['src_s3_download'] = 'ok'
                key_bytes = os.stat(local_file).st_size
                log_event['src_s3_download_bytes'] = key_bytes
            else:
                log_event['src_s3_download'] = download_status
                log_event['src_s3_download_bytes'] = -1
                sys.exit(1)

            html = convert_to_html(local_file)

            html_filename = os.path.splitext(key_name)[0] + '.html'

            local_html_file = os.path.join(tmpdir, html_filename)

            with open(local_html_file, 'w') as outfile:
                outfile.write(html)

            outfile.close()

            html_upload = upload_html(target_bucket,
                                      html_filename,
                                      local_html_file)

            if html_upload == 'ok':
                log_event['dst_s3_object'] = 's3://{}/{}'.format(target_bucket,
                                                                 html_filename)
            else:
                log_event['dst_s3_object'] = ''

            log_event['dst_s3_upload'] = html_upload

        except Exception as e:
            log_event['error_msg'] = str(e)
            print(log_event)
            return 'fail'

        finally:
            filesToRemove = os.listdir(tmpdir)

            for f in filesToRemove:
                file_path = os.path.join(tmpdir, f)
                print(f'Removing File: {file_path}')

                try:
                    os.remove(file_path)
                except OSError as e:
                    print(e)
                    print(f'Error while deleting file {file_path}')

            print(f'Removing Folder: {tmpdir}')
            os.rmdir(tmpdir)

        print(log_event)
        return 'ok'
