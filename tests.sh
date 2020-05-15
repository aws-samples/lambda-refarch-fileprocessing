#!/bin/bash


## Get Stack Resources

BUCKET_IN=$(aws cloudformation describe-stack-resource --stack-name lambda-file-refarch --logical-resource-id 'InputBucket' --query "StackResourceDetail.PhysicalResourceId" --output text)
BUCKET_OUT=$(aws cloudformation describe-stack-resource --stack-name lambda-file-refarch --logical-resource-id 'ConversionTargetBucket' --query "StackResourceDetail.PhysicalResourceId" --output text)
DYNAMO_TABLE=$(aws cloudformation describe-stack-resource --stack-name lambda-file-refarch --logical-resource-id 'SentimentTable' --query "StackResourceDetail.PhysicalResourceId" --output text)

echo "Input Bucket: $BUCKET_IN"
echo "Ouput Bucket: $BUCKET_OUT"
echo "Dynamo Table: $BUCKET_IN"

## Get Samples

TEST_FILES=(~/tests/*.md)

## Upload test samples

for f in "${arr[@]}"; do
   echo "Test file found: $f"
done



# echo "Clearing out resources of lambda-file-refarch stack..."
# echo
# echo "Cleaning up S3 buckets..." && for bucket in InputBucket ConversionTargetBucket; do
#   echo "Clearing out ${bucket}..."
#   BUCKET=$(aws cloudformation describe-stack-resource --stack-name lambda-file-refarch --logical-resource-id ${bucket} --query "StackResourceDetail.PhysicalResourceId" --output text)
#   aws s3 rm s3://${BUCKET} --recursive
#   echo
# done

# echo "Deleting CloudFormation stack..." && aws cloudformation delete-stack \
# --stack-name lambda-file-refarch

# echo "Clearing out CloudWatch Log Groups..." && for log_group in $(aws logs describe-log-groups --log-group-name-prefix '/aws/lambda/lambda-file-refarch-' --query "logGroups[*].logGroupName" --output text); do
#   echo "Removing log group ${log_group}..."
#   aws logs delete-log-group --log-group-name ${log_group}
#   echo
# done
