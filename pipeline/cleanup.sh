#!/bin/bash

command -v jq >/dev/null 2>&1 || { echo >&2 "jq is required but it's not installed.  Aborting."; exit 1; }

echo "Clearing out resources of lambda-file-refarch and Pipeline stacks..."
echo
echo "Cleaning up Application S3 buckets..." && for bucket in InputBucket ConversionTargetBucket; do
  echo "Clearing out ${bucket}..."
  BUCKET=$(aws cloudformation describe-stack-resource --stack-name lambda-file-refarch-app --logical-resource-id ${bucket} --query "StackResourceDetail.PhysicalResourceId" --output text)
  aws s3 rm s3://${BUCKET} --recursive
  echo
done

echo "Cleaning up Pipeline S3 buckets..."
BUCKET=$(aws cloudformation describe-stack-resource --stack-name lambda-file-refarch-pipeline --logical-resource-id "PipelineBucket" --query "StackResourceDetail.PhysicalResourceId" --output text)

echo

echo "Removing all versions from ${BUCKET}"

VERSIONS=`aws s3api list-object-versions  --bucket $BUCKET | jq '.Versions'`
MARKERS=`aws s3api list-object-versions  --bucket $BUCKET | jq '.DeleteMarkers'`
let COUNT=`echo $VERSIONS | jq 'length'`-1

if [ $COUNT -gt -1 ]; then
        echo "removing files from bucket"
        for i in $(seq 0 $COUNT); do
                KEY=`echo $VERSIONS | jq .[$i].Key | sed -e 's/\"//g'`
                VERSIONID=`echo $VERSIONS | jq .[$i].VersionId | sed -e 's/\"//g'`
                CMD="aws s3api delete-object --bucket $BUCKET --key $KEY --version-id $VERSIONID"
                echo ${CMD}
                $CMD
        done
fi

let COUNT=`echo $MARKERS |jq 'length'`-1

if [ $COUNT -gt -1 ]; then
        echo "removing delete markers"

        for i in $(seq 0 $COUNT); do
                KEY=`echo $MARKERS | jq .[$i].Key | sed -e 's/\"//g'`
                VERSIONID=`echo $MARKERS | jq .[$i].VersionId  | sed -e 's/\"//g'`
                CMD="aws s3api delete-object --bucket $BUCKET --key $KEY --version-id $VERSIONID"
                echo ${CMD}
                $CMD
        done
fi

echo "Deleting lambda-file-refarch-app CloudFormation stack..." && aws cloudformation delete-stack \
    --stack-name lambda-file-refarch-app

echo "Waiting for stack deletion..." && aws cloudformation wait stack-delete-complete \
    --stack-name lambda-file-refarch-app

echo "Deleting lambda-file-refarch-pipeline CloudFormation stack..." && aws cloudformation delete-stack \
    --stack-name lambda-file-refarch-pipeline

echo "Waiting for stack deletion..." && aws cloudformation wait stack-delete-complete \
    --stack-name lambda-file-refarch-pipeline

echo "Clearing out Application CloudWatch Log Groups..." && for log_group in $(aws logs describe-log-groups --log-group-name-prefix /aws/lambda/lambda-file-refarch-app- --query "logGroups[*].logGroupName" --output text); do
  echo "Removing log group ${log_group}..."
  aws logs delete-log-group --log-group-name ${log_group}
  echo
done

echo "Clearing out CodeBuild CloudWatch Log Groups..." && for log_group in $(aws logs describe-log-groups --log-group-name-prefix /aws/codebuild/lambda-file-refarch-app-build --query "logGroups[*].logGroupName" --output text); do
  echo "Removing log group ${log_group}..."
  aws logs delete-log-group --log-group-name ${log_group}
  echo
done