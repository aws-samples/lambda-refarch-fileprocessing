# AWS Lambda Reference Architecture: Real-time File Processing

The Real-time File Processing reference architecture is an general-purpose event-driven parallel data processing architecture that utilizes [AWS Lambda](https://aws.amazon.com/lambda). This architecture is ideal for workloads that need more than one data derivative of an object. This simple architecture is described in this [diagram](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda-refarch-fileprocessing.pdf) and [blog post](https://aws.amazon.com/blogs/compute/fanout-s3-event-notifications-to-multiple-endpoints/). This sample applicaton demonstrates a Markdown conversion application where Lambda is used to convert Markdown files to HTML and plain text. This sample can be created with two AWS CloudFormation templates.  

[Template One](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)
does the following:

-   Creates two Amazon Simple Storage Service (Amazon S3) buckets with dynamically-generated names from CFN:
    - Bucket 1 (`trigger-bucket`) is where we'll be putting Markdown files. The bucket name will follow the form: *stackname-eventarchive-accountid*.
    - Bucket 2 (`output-bucket`) is automatically populated after the functions run.  The bucket name will follow the form: *stackname-eventarchive-accountid-out*.

-   Creates an Amazon Simple Notification Service (Amazon SNS) topic named `event-manifold-topic`.

-   Creates an Amazon SNS topic policy which permits the S3 bucket to call the `Publish` action on the topic.

-   Creates a Lambda function named `data-processor-1` that converts Markdown to HTML.

-   Creates a Lambda function named `data-processor-2` that converts Markdown to plain text.

-   Creates an AWS Identity and Access Management (IAM) role and policy for `data-processor-1` and `data-processor-2` to assume when invoked. Permissions allow the functions to write their outputs to second S3 bucket.

-   Creates an Add Permission Lambda function to execute the
    `add-permission` action on `data-processor-1` and `data-processor-2`.
    The function permits Amazon SNS to call the `InvokeFunction` action on
   `data-processor-1` and `data-processor-2`.

-   Creates an IAM role and policy for the `add-permission` Lambda function to assume when invoked. Permissions allow the function to write output to CloudWatch Logs and execute `add-permission` on Lambda functions.

-   Creates two custom resources, each of which invoke the `add-permission` Lambda function for `data-processor-1` and `data-processor-2`.

[Template Two](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing_update.template)
does the following:

-   Configures the S3 bucket to send notifications to the trigger bucket when objects are created.

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
