#!/bin/bash

set -e

if [ -z $1 ]; then
    echo "Stack name not passed, exiting"
    exit 1
fi

STACK=$1
echo "$STACK"


function clean {

    ## Cleanup DB


    for f in "${TEST_FILES[@]}"; do

        FILE_NAME=$(cut -d "/" -f2- <<< "$f")

        echo "Removing item from DB : $FILE_NAME"

        aws dynamodb delete-item --table-name $DYNAMO_TABLE \
        --key "{\"id\": {\"S\": \"s3://$BUCKET_IN/$FILE_NAME\"}}"


        if [ $? -ne 0 ]; then
            echo -e "Remove item failed" ; exit 1
        fi

    done

    ## Cleanup Output


    for f in "${TEST_FILES[@]}"; do

      FILE_NAME=$(cut -d "/" -f2- <<< "$f")

      echo "Removing from output : ${FILE_NAME/md/html}"

      aws s3 rm s3://"$BUCKET_OUT"/"${FILE_NAME/md/html}"

        if [[ $? -ne 0 ]]; then
          echo -e "File not processed" ; exit 1
        fi

    done

    ## Cleanup Input


    for f in "${TEST_FILES[@]}"; do

      FILE_NAME=$(cut -d "/" -f2- <<< "$f")

      echo "Removing from input: $FILE_NAME"

      aws s3 rm s3://"$BUCKET_IN"/"$FILE_NAME"

        if [[ $? -ne 0 ]]; then
          echo -e "File not processed" ; exit 1
        fi


    done


}


## Get Stack Resources

BUCKET_IN=$(aws cloudformation describe-stack-resource \
--stack-name "$STACK" --logical-resource-id 'InputBucket' \
--query "StackResourceDetail.PhysicalResourceId" \
--output text)


BUCKET_OUT=$(aws cloudformation describe-stack-resource \
--stack-name "$STACK" \
--logical-resource-id 'ConversionTargetBucket' \
--query "StackResourceDetail.PhysicalResourceId" \
--output text)


DYNAMO_TABLE=$(aws cloudformation describe-stack-resource \
--stack-name "$STACK" --logical-resource-id 'SentimentTable' \
--query "StackResourceDetail.PhysicalResourceId" \
--output text)


echo "Found Input Bucket: $BUCKET_IN"
echo "Found Ouput Bucket: $BUCKET_OUT"
echo "Found DynamoDB Table: $DYNAMO_TABLE"

## Get Samples

TEST_FILES=(tests/sample-*.md)

## Upload test samples

for f in "${TEST_FILES[@]}"; do

    FILE_NAME=$(cut -d "/" -f2- <<< "$f")

    echo "Upload sample : $FILE_NAME"

    aws s3 cp $f s3://"$BUCKET_IN"/"$FILE_NAME"

    if [ $? -ne 0 ]; then
        echo -e "Upload Failed" ; exit 1
    fi

done


# Give Lambda a chance to execute or wait for last file to get to output.

END=$((SECONDS+30))

echo "Waiting for execution"

while [ $SECONDS -lt $END ]

do

    FILE_NAME=$(cut -d "/" -f2- <<< ${TEST_FILES[*]: -1})

    EXISTS=$(aws s3api head-object --bucket $BUCKET_OUT --key ${FILE_NAME/md/html}) || NOT_EXIST=true

    if [[ $EXISTS ]]; then
        echo "File exists, continuing"
        break
    fi

    echo "File doesn't exist yet... Waiting for timeout."
    sleep 1

done


# Check for files in output bucket

for f in "${TEST_FILES[@]}"; do

    FILE_NAME=$(cut -d "/" -f2- <<< "$f")

    echo "Checking for Output : ${FILE_NAME/md/html}"

    EXISTS=(aws s3api head-object --bucket $BUCKET_OUT --key ${FILE_NAME/md/html}) || $NOT_EXIST=true

    if [[ -z $EXISTS ]]; then
        echo -e "File ${FILE_NAME/md/html} not processed" ; exit 1
    fi

    echo "${FILE_NAME/md/html} found"

done

# Check DynamoDB for Sentiment

for f in "${TEST_FILES[@]}"; do

    FILE_NAME=$(cut -d "/" -f2- <<< "$f")

    echo "Checking for Sentiment : $FILE_NAME"

    SENTIMENT=$(aws dynamodb get-item --table-name $DYNAMO_TABLE \
    --projection-expression "overall_sentiment" \
    --key "{\"id\": {\"S\": \"s3://$BUCKET_IN/$FILE_NAME\"}}")

    if [[ -z $SENTIMENT  ]]; then
      echo -e "No Sentiment" ;  exit 1
    fi

    echo $SENTIMENT

done

# Call Clean Up
clean
