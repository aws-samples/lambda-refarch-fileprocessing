# AWS Lambda Reference Architecture: Real-time File Processing

The Real-time File Processing reference architecture is an general-purpose event-driven parallel data processing architecture that utilizes [AWS Lambda](https://aws.amazon.com/lambda). This architecture is ideal for workloads that need more than one data derivative of an object. This simple architecture is described in this [diagram](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda-refarch-fileprocessing.pdf) and [blog post](https://aws.amazon.com/blogs/compute/fanout-s3-event-notifications-to-multiple-endpoints/). This sample applicaton demonstrates a Markdown conversion application where Lambda is used to convert Markdown files to HTML and plain text.

## AWS CloudFormation Template

[![Launch into Lambda ETL into North Virginia with CloudFormation](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/images/cloudformation-launch-stack-button.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=lambda-file-processing&templateURL=https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)

[The provided template](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)
creates the following resources:

-   Two Amazon Simple Storage Service (Amazon S3) buckets with dynamically-generated names based on the CloudFormation stack name and the account ID where the stack is launched:
    - `InputBucket` is used to hold the raw Markdown files to be processed and is configured to send a notification to the `InputNotificationTopic` when a new object is created.
    - `OutputBucket` is populated by the processor functions that run in response to each object added to `InputBucket`.

-   An Amazon Simple Notification Service (Amazon SNS) topic used to invoke multiple Lambda functions in response to each object creation notification.

-   An Amazon SNS topic policy which permits `InputBucket` to call the `Publish` action on the topic.

-   Two Lambda functions that process each object uploaded to `InputBucket`:
    - `ProcessorFunctionOne` converts Markdown files to HTML.
    - `ProcessorFunctionTwo` converts Markdown files to plain text.

-   An AWS Identity and Access Management (IAM) role for the two Lambda functions to assume when invoked.
-   An IAM policy associated with the role that allows the functions to get objects from `InputBucket`, put object to `OutputBucket` and log to Amazon CloudWatch.
-  Two Lambda permissions that enable Amazon SNS to invoke both processor functions.

## Instructions

**Important:** Because the AWS CloudFormation stack name is used in the name of the S3 buckets, that stack name must only contain lowercase letters. Please use lowercase letters when typing the stack name. The provided CloudFormation template retreives its Lambda code from a bucket in the us-east-1 region. To launch this sample in another region, please modify the template and upload the Lambda code to a bucket in that region.

**Step 1** – Create an AWS CloudFormation Stack with Template One.

**Step 2** – Update Template One with Template Two (Update Stack).

**Step 3** – Upload a Markdown file to the `trigger-bucket` by using the AWS Command Line Interface:

```bash
$ aws s3 cp <some_file> s3://trigger-bucket
```

**Step 4** – View the CloudWatch Log events for the `data-processor-1` and `data-processor-2` Lambda functions for evidence that both functions were triggered by the Amazon SNS message from the Amazon S3 upload event.

**Step 5** Check your `output-bucket` and confirm both new files are created:

```bash
$ aws s3 ls s3://output-bucket
```


## Worth Noting

The `add-permission` Lambda function will send output to CloudWatch Logs during Template One, showing the exchange between AWS CloudFormation and a Lambda custom resource.

The `data-processor-1` and `data-processor-2` Lambda functions will show the Amazon S3 test event notification sent to the topic after Template Two.

## License

This reference architecture sample is licensed under Apache 2.0.
