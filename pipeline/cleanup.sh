#!/bin/bash


echo "Clearing out resources of lambda-file-refarch and Pipeline stacks..."
echo
echo "Cleaning up Application S3 buckets..." && for bucket in InputBucket ConversionTargetBucket; do
  echo "Clearing out ${bucket}..."
  BUCKET=$(aws cloudformation describe-stack-resource --stack-name lambda-file-refarch --logical-resource-id ${bucket} --query "StackResourceDetail.PhysicalResourceId" --output text)
  aws s3 rm s3://${BUCKET} --recursive
  echo
done

echo "Cleaning up Pipeline S3 buckets..."
BUCKET=$(aws cloudformation describe-stack-resource --stack-name lambda-file-refarch-pipeline --logical-resource-id "PipelineBucket" --query "StackResourceDetail.PhysicalResourceId" --output text)

echo

echo "Removing all VERSIONS from ${BUCKET}"

VERSIONS=`aws s3api list-object-VERSIONS --bucket $BUCKET |jq '.VERSIONS'`
MARKERS=`aws s3api list-object-VERSIONS --bucket $BUCKET |jq '.DeleteMARKERS'`
let COUNT=`echo $VERSIONS |jq 'length'`-1

if [ $COUNT -gt -1 ]; then
        echo "removing files from bucket"
        for i in $(seq 0 $COUNT); do
                KEY=`echo $VERSIONS | jq .[$i].KEY |sed -e 's/\"//g'`
                VERSIONID=`echo $VERSIONS | jq .[$i].VERSIONID |sed -e 's/\"//g'`
                CMD="aws s3api delete-object --bucket $BUCKET --KEY $KEY --version-id $VERSIONID"
                echo $CMD
                $CMD
        done
fi

let COUNT=`echo $MARKERS |jq 'length'`-1

if [ $COUNT -gt -1 ]; then
        echo "removing delete MARKERS"

        for i in $(seq 0 $COUNT); do
                KEY=`echo $MARKERS | jq .[$i].KEY |sed -e 's/\"//g'`
                VERSIONID=`echo $MARKERS | jq .[$i].VERSIONID |sed -e 's/\"//g'`
                CMD="aws s3api delete-object --bucket $BUCKET --KEY $KEY --version-id $VERSIONID"
                echo $CMD
                $CMD
        done
fi

echo "Deleting lambda-file-refarch CloudFormation stack..." && aws cloudformation delete-stack \
    --stack-name lambda-file-refarch

echo "Waiting for stack deletion..." && aws cloudformation wait stack-delete-complete \
    --stack-name lambda-file-refarch

echo "Deleting lambda-file-refarch-pipeline CloudFormation stack..." && aws cloudformation delete-stack \
    --stack-name lambda-file-refarch-pipeline

echo "Waiting for stack deletion..." && aws cloudformation wait stack-delete-complete \
    --stack-name lambda-file-refarch-pipeline

echo "Clearing out Application CloudWatch Log Groups..." && for log_group in $(aws logs describe-log-groups --log-group-name-prefix /aws/lambda/lambda-file-refarch- --query "logGroups[*].logGroupName" --output text); do
  echo "Removing log group ${log_group}..."
  aws logs delete-log-group --log-group-name ${log_group}
  echo
done

echo "Clearing out CodeBuild CloudWatch Log Groups..." && for log_group in $(aws logs describe-log-groups --log-group-name-prefix /aws/codebuild/lambda-file-refarch- --query "logGroups[*].logGroupName" --output text); do
  echo "Removing log group ${log_group}..."
  aws logs delete-log-group --log-group-name ${log_group}
  echo
done