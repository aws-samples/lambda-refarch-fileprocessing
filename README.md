# Serverless Reference Architecture: Real-time File Processing
README Languages:  [DE](README/README-DE.md) | [ES](README/README-ES.md) | [FR](README/README-FR.md) | [IT](README/README-IT.md) | [JP](README/README-JP.md) | [KR](README/README-KR.md) |
[PT](README/README-PT.md) | [RU](README/README-RU.md) |
[CN](README/README-CN.md) | [TW](README/README-TW.md)

The Real-time File Processing reference architecture is a general-purpose, event-driven, parallel data processing architecture that uses [AWS Lambda](https://aws.amazon.com/lambda). This architecture is ideal for workloads that need more than one data derivative of an object. 

In this example application we deliver the notes from an interview in markdown format into S3 and we utilise CloudWatch Events to trigger multiple processing flows.

## Architectural Diagram

![Reference Architecture - Real-time File Processing](img/lambda-refarch-fileprocessing-simple.png)

## Application Components

### Event Trigger
Unlike batch processing, in this architecture we process each individual file as it arrives. To achive this we utilise [CloudWatch Events](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/WhatIsCloudWatchEvents.html) and [CloudTrail](https://aws.amazon.com/cloudtrail/). We write a CloudWatch Events rule which checks for S3 PutObject API calls into our Source Bucket from CloudTrail. Everytime the PutObject API is called this creates a CloudTrail log which our rule translates into an event represented as a JSON object. In our rule we also define targets which our JSON event object is delivered to, which in this scenario is 4 seperate [SQS Queues](https://aws.amazon.com/sqs/) for 4 different worflows. Other target types include AWS Lambda Functions, Kinesis Data Streams, Simple Notification Service, Step Functions state machines, ECS tasks refer to [What is Amazon CloudWatch Events?](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/WhatIsCloudWatchEvents.html) for more information about eligible targets.

### Conversion WorkFlow

For this workflow the target of our JSON object decribing the S3 PutObject event is an SQS queue. Sending to SQS first rather than directly to Lambda allows for more control of Lambda invocations and better error handling.

Lambda polls our queue and when messages are available it will send them to our function. Lambda can automatically scale with the number of messages on the queue. Refer to [Using AWS Lambda with Amazon SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html) for more details.

If our Lambda fails to process the messages we can configure SQS to send to a dead-letter queue for inspection and reprocessing.

Once the function has the message this is parsed. The JSON event object contains information such as the S3 bucket and object key and object size.  

Our function business logic uses this information to retrieve the file from S3 using the [Python AWS SDK (boto3)](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html?id=docs_gateway) and store it in a temporary location within the function environment. The path of the file is then passed to a python function which reads the file contents and converts it to HTML using the Python [Markdown Library](https://pypi.org/project/Markdown/). We then generate the filename for the new HTML file and write it to our temporary location. Finally we upload the new html file to the HTML Bucket.


### Sentiment Analysis Workflow

Here we are using our AI/ML service [Amazon Comprehend](https://aws.amazon.com/comprehend/) which is a machine learning powered service that makes it easy to find insights and relationships in text. We can use the Sentiment Analysis API in order to understand if the questions the interviewer asked had positive or negative responses.

This workflow uses the same SQS to Lambda Function pattern as the coversion workflow. Here our business logic downloads the file and extracts the content of the file and sends it to the Comprehend Sentiment Analysis API. This returns a Sentiment and a confidence Score which Describes the level of confidence that Amazon Comprehend has in the accuracy of its detection of sentiments.

Once we have our sentiment we persist the result to our [DynamoDB](https://aws.amazon.com/dynamodb/) table. 


### Search Indexing Workflow
TODO

### Replay Workflow

TODO


## Running the Example

You can use the provided [AWS SAM template] 

TODO **Insert CFN Template Link** 

to launch a stack that demonstrates the Lambda file processing reference architecture. Details about the resources created by this template are provided in the *CloudFormation Template Resources* section of this document.

**Important** Because the AWS CloudFormation stack name is used in the name of the Amazon Simple Storage Service (Amazon S3) buckets, that stack name must only contain lowercase letters. Use lowercase letters when typing the stack name. The provided CloudFormation template retrieves its Lambda code from a bucket in the us-east-1 region. To launch this sample in another region, please modify the template and upload the Lambda code to a bucket in that region.


Choose **Launch Stack** to launch the template in the us-east-1 region in your account:

TODO Update Link

[![Launch Lambda File Processing into North Virginia with CloudFormation](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/images/cloudformation-launch-stack-button.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=lambda-file-processing&templateURL=https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)

## Using SAM

Install the dependencies for lambda

```bash
cd src/conversion && pip install -r requirements.txt -t .
cd src/sentiment && pip install -r requirements.txt -t .
```

Run SAM package (equivalent to aws cloudformation package)

```bash
sam package \
    --template-file file_processing.yml \
    --output-template-file packaged-template.yml \
    --s3-bucket <YOUR S3 CODE BUCKET>
```


Deploy the SAM template

```bash
sam deploy \
    --template-file packaged-template.yml \
    --stack-name lambda-file-refarch \
    --capabilities CAPABILITY_IAM
```


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

## CloudFormation Template Resources

### Resources
[The provided template](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)
creates the following resources:

- **InputBucket** - An S3 bucket that holds the raw Markdown files. Uploading a file to this bucket will trigger processing functions.

- **CloudTrailBucket** - An S3 bucket that is used to store CloudTrail data.

- **InputBucketTrail** - An CloudTrail definition that captures events put into the **CloudTrailBucket**.

- **CloudTrailBucketPolicy** - A S3 policy which permits the AWS CloudTrail service to write data to the **CloudTrailBucket**.

- **FileProcessingQueuePolicy** - A SQS policy that allows the **FileProcessingRule** to publish events to the **ConversionQueue** and **SentimentQueue**.

- **FileProcessingRule** - A CloudWatch Events Rule that monitors CloudTrail `PubObject` events from the **InputBucket**.

- **ConversionQueue** - A SQS queue that is used to store events for conversion from markdown to HTML.

- **ConversionDlq** - TBD.

- **ConversionFunction** - A Lambda function that takes the input file, converts it to HTML, and stores the resulting file to **ConversionTargetBucket**.

- **ConversionTargetBucket** - A S3 bucket that stores the converted HTML.

- **SentimentQueue** - A SQS queue that is used to store events for sentiment analysis processing.

- **SentimentDlq** - TBD.

- **SentimentFunction** - A Lambda function that takes the input file, performs sentiment analysis, and stores the output to the **SentimentTable**.

- **SentimentTable** - A DynamoDB table that stores the input file along with the sentiment.


## License

This reference architecture sample is licensed under Apache 2.0.
