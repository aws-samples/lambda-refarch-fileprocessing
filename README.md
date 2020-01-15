# Serverless Reference Architecture: Real-time File Processing

The Real-time File Processing reference architecture is a general-purpose, event-driven, parallel data processing architecture that uses [AWS Lambda](https://aws.amazon.com/lambda). This architecture is ideal for workloads that need more than one data derivative of an object. 

In this example application we deliver the notes from an interview in Markdown format to S3.  CloudWatch Events is used to trigger multiple processing flows - one to convert and persist Markdown files to HTML and another to detect and persist sentiment.

## Architectural Diagram

![Reference Architecture - Real-time File Processing](img/lambda-refarch-fileprocessing-simple.png)

## Application Components

### Event Trigger

Unlike batch processing, in this architecture we process each individual file as it arrives. To achive this we utilise [CloudWatch Events](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/WhatIsCloudWatchEvents.html) and [CloudTrail](https://aws.amazon.com/cloudtrail/). A CloudWatch Events rule  checks for S3 PutObject API calls into our Source Bucket using CloudTrail data. CloudTrail records when PutObject API is called.  Our rule translates this record into an event, represented as a JSON object. We also define targets in our rule and deliver our JSON event to 2 seperate [SQS Queues](https://aws.amazon.com/sqs/), representing 2 different worflows. Other target types include AWS Lambda Functions, Kinesis Data Streams, Simple Notification Service, Step Functions state machines, and ECS tasks. Refer to [What is Amazon CloudWatch Events?](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/WhatIsCloudWatchEvents.html) for more information about eligible targets.

### Conversion Workflow

We target a SQS queue for this workflow. Sending the JSON event to SQS first rather than directly to Lambda allows for more control of Lambda invocations and better error handling.

The Lambda service polls our queue. When messages are available it will send them to our function. Lambda can automatically scale with the number of messages on the queue. Refer to [Using AWS Lambda with Amazon SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html) for more details.

If our Conversion Lambda function fails to process the messages, SQS sends the event to a dead-letter queue (DLQ) for inspection and reprocessing. A CloudWatch Alarm is configured to send notification to an email address when there are any messages in the Conversion DLQ.

Our function business logic uses this information to retrieve the file from S3 using the [Python AWS SDK (boto3)](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html?id=docs_gateway) and store it in a temporary location within the function execution environment. The path of the file is then passed to a python function which reads the file contents and converts it to HTML using the Python [Markdown Library](https://pypi.org/project/Markdown/). We then generate the filename for the new HTML file and write it to our temporary location. Finally we upload the new html file to the HTML Bucket.


### Sentiment Analysis Workflow

We are using AWS' AI/ML service [Amazon Comprehend](https://aws.amazon.com/comprehend/) which is a machine learning powered service that makes it easy to find insights and relationships in text. We use the Sentiment Analysis API to understand whether interview responses are positive or negative.

The Sentiment workflow uses the same SQS-to-Lambda Function pattern as the Coversion workflow. Our function downloads the interview file, extracts the content, and sends it to the Comprehend Sentiment Analysis API. This returns a Sentiment and a confidence score which describes the level of confidence that Amazon Comprehend has in the accuracy of its detection of sentiments.

Once we have our sentiment we persist the result to our [DynamoDB](https://aws.amazon.com/dynamodb/) table.

If our Sentiment Lambda function fails to process the messages, SQS sends the event to a dead-letter queue (DLQ) for inspection and reprocessing. A CloudWatch Alarm is configured to send notification to an email address when there are any messages in the Sentiment DLQ.


## Running the Example

You can use the provided [AWS SAM template](./template.yml) to launch a stack that demonstrates the Lambda file processing reference architecture. Details about the resources created by this template are provided in the *SAM Template Resources* section of this document.


### Using SAM to Build and Deploy the Application

#### Build

The AWS SAM CLI comes with abstractions for a number of Lambda runtimes to build your dependencies, and copies the source code into staging folders so that everything is ready to be packaged and deployed. The *sam build* command builds any dependencies that your application has, and copies your application source code to folders under *.aws-sam/build* to be zipped and uploaded to Lambda. 

```bash
sam build --use-container
```

#### Package

Next, run *sam package*.  This command takes your Lambda handler source code and any third-party dependencies, zips everything, and uploads the zip file to your Amazon S3 bucket. That bucket and file location are then noted in the packaged-template.yaml file. You use the generated packaged-template.yaml file to deploy the application in the next step. 

```bash
sam package \
    --output-template-file packaged-template.yml \
    --s3-bucket bucketname
```

**Note**

For *bucketname* in this command, you need an Amazon S3 bucket that the sam package command can use to store the deployment package. The deployment package is used when you deploy your application in a later step. If you need to create a bucket for this purpose, run the following command to create an Amazon S3 bucket: 

```bash
aws s3 mb s3://bucketname --region region  # Example regions: us-east-1, ap-east-1, eu-central-1, sa-east-1
```

#### Deploy

This command deploys your application to the AWS Cloud. It's important that this command explicitly includes both of the following:

  * The AWS Region to deploy to. This Region must match the Region of the Amazon S3 source bucket.

  * The CAPABILITY_IAM parameter, because creating new Lambda functions involves creating new IAM roles.

```bash
sam deploy \
    --template-file packaged-template.yml \
    --stack-name lambda-file-refarch \
    --region region \
    --tags Project=lambda-refarch-fileprocessing \
    --parameter-overrides AlarmRecipientEmailAddress=<your email address> \
    --capabilities CAPABILITY_IAM
```

You will receive an email asking you to confirm subscription to the `lambda-file-refarch-AlarmTopic` SNS topic that will receive alerts should either the `ConversionDlq` SQS queue or `SentimentDlq` SQS queue receive messages.

## Testing the Example

After you have created the stack using the CloudFormation template, you can test the system by uploading a Markdown file to the InputBucket that was created in the stack. You can use the sample-1.md and sample-2.md files in the repository as example files. After the files have been uploaded, you can see the resulting HTML file in the output bucket of your stack. You can also view the CloudWatch logs for each of the functions in order to see the details of their execution.

You can use the following commands to copy a sample file from the provided S3 bucket into the input bucket of your stack.

```bash
INPUT_BUCKET=$(aws cloudformation describe-stack-resource --stack-name lambda-file-refarch --logical-resource-id InputBucket --query "StackResourceDetail.PhysicalResourceId" --output text)
aws s3 cp ./sample-1.md s3://${INPUT_BUCKET}/sample-1.md
aws s3 cp ./sample-2.md s3://${INPUT_BUCKET}/sample-2.md
```

Once the input files has been uploaded to the input bucket, a series of events are put into motion.

1. The input Markdown files are converted and stored in a separate S3 bucket.
```
OUTPUT_BUCKET=$(aws cloudformation describe-stack-resource --stack-name lambda-file-refarch --logical-resource-id ConversionTargetBucket --query "StackResourceDetail.PhysicalResourceId" --output text)
aws s3 ls s3://${OUTPUT_BUCKET}
```

2. The input Markdown files are analyzed and their sentiment published to a DynamoDB table.
```
DYNAMO_TABLE=$(aws cloudformation describe-stack-resource --stack-name lambda-file-refarch --logical-resource-id SentimentTable --query "StackResourceDetail.PhysicalResourceId" --output text)
aws dynamodb scan --table-name ${DYNAMO_TABLE} --query "Items[*]"
```

You can also view the CloudWatch logs generated by the Lambda functions.

## Cleaning Up the Example Resources

To remove all resources created by this example, do the following:

### Delete Objects in the Input and Output Buckets.

```bash
for bucket in InputBucket CloudTrailBucket ConversionTargetBucket; do
  echo "Clearing out ${bucket}..."
  BUCKET=$(aws cloudformation describe-stack-resource --stack-name lambda-file-refarch --logical-resource-id ${bucket} --query "StackResourceDetail.PhysicalResourceId" --output text)
  aws s3 rm s3://${BUCKET} --recursive
  echo
done
```

### Delete the CloudFormation Stack

```bash
aws cloudformation delete-stack \
--stack-name lambda-file-refarch
```

### Delete the CloudWatch Log Groups

```bash
for log_group in $(aws logs describe-log-groups --log-group-name-prefix '/aws/lambda/lambda-file-refarch-' --query "logGroups[*].logGroupName" --output text); do
  echo "Removing log group ${log_group}..."
  aws logs delete-log-group --log-group-name ${log_group}
  echo
done
```

## SAM Template Resources

### Resources
[The provided template](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/packaged-template.yml)
creates the following resources:

- **InputBucket** - An S3 bucket that holds the raw Markdown files. Uploading a file to this bucket will trigger processing functions.

- **CloudTrailBucket** - An S3 bucket that is used to store CloudTrail data.

- **InputBucketTrail** - An CloudTrail definition that captures events put into the **CloudTrailBucket**.

- **CloudTrailBucketPolicy** - A S3 policy which permits the AWS CloudTrail service to write data to the **CloudTrailBucket**.

- **FileProcessingQueuePolicy** - A SQS policy that allows the **FileProcessingRule** to publish events to the **ConversionQueue** and  **SentimentQueue**.

- **FileProcessingRule** - A CloudWatch Events Rule that monitors CloudTrail `PutObject` events to the **InputBucket**.

- **ConversionQueue** - A SQS queue that is used to store events for conversion from Markdown to HTML.

- **ConversionDlq** - A SQS queue that is used to capture messages that cannot be processed by the **ConversionFunction**.  The *RedrivePolicy* on the **ConversionQueue** is used to manage how traffic makes it to this queue.

- **ConversionFunction** - A Lambda function that takes the input file, converts it to HTML, and stores the resulting file to **ConversionTargetBucket**.

- **ConversionTargetBucket** - A S3 bucket that stores the converted HTML.

- **SentimentQueue** - A SQS queue that is used to store events for sentiment analysis processing.

- **SentimentDlq** - A SQS queue that is used to capture messages that cannot be processed by the **SentimentFunction**.  The *RedrivePolicy* on the **SentimentQueue** is used to manage how traffic makes it to this queue.

- **SentimentFunction** - A Lambda function that takes the input file, performs sentiment analysis, and stores the output to the **SentimentTable**.

- **SentimentTable** - A DynamoDB table that stores the input file along with the sentiment.

- **AlarmTopic** - A SNS topic that has an email as a subscriber.  This topic is used to receive CloudWatch Alarms.

- **ConversionDlqAlarm** - A CloudWatch Alarm that detects when there there are any messages sent to the **ConvesionDlq** within a 1 minute period and sends notification to the **AlarmTopic**.

- **SentimentDlqAlarm** - A CloudWatch Alarm that detects when there there are any messages sent to the **SentimentDlq** within a 1 minute period and sends notification to the **AlarmTopic**.

- **ConversionQueueAlarm** - A CloudWatch Alarm that detect when there are too many messages in the **ConversionQueue** and sends notification to the **AlarmTopic**.

- **SentimentQueueAlarm** - A CloudWatch Alarm that detect when there are too many messages in the **SentimentQueue** and sends notification to the **AlarmTopic**.

- **ConversionFunctionErrorRateAlarm** - A CloudWatch Alarm that detects when the error rate for **ConversionFunction** is too high and sends notification to the **AlarmTopic**.

- **SentimentFunctionErrorRateAlarm** - A CloudWatch Alarm that detects when the error rate for **SentimentFunction** is too high and sends notification to the **AlarmTopic**.


## License

This reference architecture sample is licensed under Apache 2.0.
