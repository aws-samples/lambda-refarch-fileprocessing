#!/bin/bash


echo "Clearing out resources of lambda-file-refarch stack..."
echo
echo "Cleaning up S3 buckets..." && for bucket in InputBucket ConversionTargetBucket; do
  echo "Clearing out ${bucket}..."
  BUCKET=$(aws cloudformation describe-stack-resource --stack-name lambda-file-refarch --logical-resource-id ${bucket} --query "StackResourceDetail.PhysicalResourceId" --output text)
  aws s3 rm s3://${BUCKET} --recursive
  echo
done

echo "Deleting CloudFormation stack..." && aws cloudformation delete-stack \
--stack-name lambda-file-refarch

echo "Clearing out CloudWatch Log Groups..." && for log_group in $(aws logs describe-log-groups --log-group-name-prefix '/aws/lambda/lambda-file-refarch-' --query "logGroups[*].logGroupName" --output text); do
  echo "Removing log group ${log_group}..."
  aws logs delete-log-group --log-group-name ${log_group}
  echo
done
