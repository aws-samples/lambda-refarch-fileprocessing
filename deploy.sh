#!/bin/bash

if (( ${#} < 3)); then
  echo "USAGE: ${0} s3_package_bucket_name aws_region recipient_email"
  exit 1
fi

###
# Variables
###
export SAM_TEMPLATE="template.yml"
export PACKAGED_TEMPLATE="packaged-template.yml"
export STACK_NAME="lambda-file-refarch"
export S3_CODE_BUCKET=${1}
export AWS_REGION=${2}
export RECIPIENT_EMAIL=${3}
export SAM_BUILD_ARG=${4} # Possible to pass in --skip-pull-image if docker image is already local
export FILE_TO_UPDATE="src/conversion/conversion.py"

###
# Functions
###
function sam-runner {
    sam build --use-container ${SAM_BUILD_ARG}
    sam package --output-template-file ${PACKAGED_TEMPLATE} \
        --s3-bucket ${S3_CODE_BUCKET} # 2> /dev/null
    sam deploy \
        --template-file ${PACKAGED_TEMPLATE} \
        --stack-name ${STACK_NAME} \
        --region ${AWS_REGION} \
        --tags Project=lambda-refarch-fileprocessing \
        --parameter-overrides AlarmRecipientEmailAddress=${RECIPIENT_EMAIL} \
        --capabilities CAPABILITY_IAM
}

###
# Main body
###

# Need to run two passes of the CF template to mitigate race condition.
# Please refer to https://aws.amazon.com/premiumsupport/knowledge-center/unable-validate-destination-s3/
# for more detailed information.
sed -i '' '30,33 s/^/#/' ${SAM_TEMPLATE}
echo '' >> ${FILE_TO_UPDATE}
sam-runner
echo
sed -i '' '30,33 s/^#//' ${SAM_TEMPLATE}
echo '' >> ${FILE_TO_UPDATE}
sam-runner
git checkout ${FILE_TO_UPDATE}
echo