import json
import os

import boto3
import botocore
import markdown

max_object_size = 104857600 # 100MB = 104857600 bytes

target_bucket = os.getenv('TARGET_BUCKET')

s3_resource = boto3.resource('s3')


def check_s3_object_size(bucket, key_name):
    try:
        size = s3_resource.Object(bucket, key_name).content_length
    except Exception as e:
        print('Error: {}'.format(str(e)))
        size = 'NaN'
    
    return size

def get_s3_object(bucket, key_name):
    try:
        s3_resource.Bucket(bucket).download_file(key_name, '/tmp/{}'.format(key_name))
        return 'ok'
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            return 'Error: s3://{}/{} does not exist'.format(bucket, key_name)
        else:
            return 'Error: {}'.format(str(e))

def convert_to_html(file):
    try:
        file_string = open(file).read()
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
    log_event = {}

    try:
        json_body = json.loads(event['Records'][0]['body'])
        request_params = json_body['detail']['requestParameters']
        bucket_name = request_params['bucketName']
        key_name = request_params['key']
        log_event['source_s3_bucket_name'] = bucket_name
        log_event['source_s3_key_name'] = key_name

        size = check_s3_object_size(bucket_name, key_name)

        download_status = get_s3_object(bucket_name, key_name)

        local_file = '/tmp/{}'.format(key_name)
        
        if download_status == 'ok':
            log_event['source_s3_download'] = 'ok'
            key_bytes = os.stat(local_file).st_size
            log_event['source_s3_download_bytes'] = key_bytes
        else:
            log_event['source_s3_download'] = download_status
            log_event['source_s3_download_bytes'] = -1

        html = convert_to_html(local_file)

        html_filename = os.path.splitext(key_name)[0] + '.html'

        html_file = '/tmp/{}'.format(html_filename)

        with open(html_file, 'w') as outfile:
            outfile.write(html)

        html_upload = upload_html(target_bucket, html_filename, html_file)

        if html_upload == 'ok':
            log_event['dest_s3_object'] = 's3://{}/{}'.format(target_bucket, html_filename)
        else:
            log_event['dest_s3_object'] = ''

        log_event['dest_s3_upload'] = html_upload

    except Exception as e:
        log_event['error_msg'] = str(e)
        print(log_event)
        return 'fail'
    print(log_event)
    return 'ok'
