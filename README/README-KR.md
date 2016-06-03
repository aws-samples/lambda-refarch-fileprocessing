# 서버 없는 레퍼런스 아키텍처: 실시간 파일 처리

실시간 파일 처리 레퍼런스 아키텍처는 이벤트 중심의 범용 병렬 데이터 처리 아키텍처이며 [AWS Lambda](https://aws.amazon.com/lambda)를 사용합니다. 이 아키텍처는 객체의 데이터 파생이 하나 이상 필요한 워크로드에 적합합니다. 이 간단한 아키텍처는 이 [diagram](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda-refarch-fileprocessing.pdf) 및 AWS Compute 블로그의 ["Fanout S3 Event Notifications to Multiple Endpoints" blog post](https://aws.amazon.com/blogs/compute/fanout-s3-event-notifications-to-multiple-endpoints/)에 설명되어 있습니다. 이 단순한 애플리케이션은 Lambda를 사용하여 Markdown 파일을 HTML 및 일반 텍스트로 변환하는 Markdown 변환 애플리케이션을 보여줍니다.

## 예제 실행

제공된 [AWS CloudFormation template](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)을 사용하여 Lambda 파일 처리 레퍼런스 아키텍처를 보여주는 스택을 시작할 수 있습니다. 이 템플릿을 통해 생성된 리소스에 대한 세부 정보는 본 문서의 *CloudFormation 템플릿 리소스* 단원에서 제공됩니다.

**중요** AWS CloudFormation 스택 이름은 Amazon Simple Storage Service(Amazon S3) 버킷에서 사용되므로 이 스택 이름은 소문자만 포함해야 합니다. 스택 이름을 입력할 때는 소문자만 사용하십시오. 제공된 CloudFormation 템플릿은 us-east-1 리전의 버킷에서 Lambda 코드를 가져옵니다. 이 샘플을 다른 리전에서 시작하려면 템플릿을 수정하고 Lambda 코드를 해당 리전의 버킷에 업로드하십시오.


**Launch Stack**을 선택하여 계정의 us-east-1 리전에서 템플릿을 시작합니다.

[![Launch Lambda File Processing into North Virginia with CloudFormation](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/images/cloudformation-launch-stack-button.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=lambda-file-processing&amp;templateURL=https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)

그 밖에도 다음 명령을 사용하여 AWS CLI를 사용하여 스택을 시작할 수 있습니다. 이 단계를 실행하기 위해 이미 [installed the AWS CLI](http://docs.aws.amazon.com/cli/latest/userguide/installing.html)를 완료했다고 가정합니다.

```bash
aws cloudformation create-stack \
    --stack-name lambda-file-processing \
    --template-url https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template \
    --capabilities CAPABILITY_IAM
```

## 예제 테스트

CloudFormation 템플릿을 사용하여 스택을 만든 후 Markdown 파일을 스택에 만들어진 InputBucket으로 업로드하여 시스템을 테스트할 수 있습니다. 리포지토리의 이 README.md 파일을 예제 파일로 사용할 수 있습니다. 파일을 업로드한 후 스택의 출력 버킷에서 결과 HTML과 일반 텍스트 파일을 확인할 수 있습니다. 각 함수의 CloudWatch 로그를 통해 각각의 실행 세부 정보를 볼 수도 있습니다.

다음 명령을 사용하여 제공된 S3 버킷에서 샘플 파일을 스택의 입력 버킷으로 복사할 수 있습니다.

```
BUCKET=$(aws cloudformation describe-stack-resource --stack-name lambda-file-processing --logical-resource-id InputBucket --query "StackResourceDetail.PhysicalResourceId" --output text)
aws s3 cp s3://awslambda-reference-architectures/file-processing/example.md s3://$BUCKET/example.md
```

파일을 입력 버킷으로 업로드한 후 출력 버킷을 검사하여 렌더링된 HTML과 Lambda 함수에 의해 생성된 일반 텍스트 출력 파일을 확인할 수 있습니다.

Lambda 함수에 의해 생성된 CloudWatch 로그도 볼 수 있습니다.

## 예제 리소스 정리

이 예제에서 생성된 모든 리소스를 제거하려면 다음을 수행합니다.

1. 입력 및 출력 버킷에서 모든 객체를 삭제합니다.
1. CloudFormation 스택을 삭제합니다.
1. 두 프로세서 함수에 대한 실행 정보가 포함된 CloudWatch 로그 그룹을 삭제합니다.



## CloudFormation 템플릿 리소스

### 파라미터
- **CodeBucket** - 스택의 리전에 있는 S3 버킷의 이름이며 두 Lambda 함수(ProcessorFunctionOne 및 ProcessorFunctionTwo)에 대한 코드가 포함되어 있습니다. 관리형 버킷 `awslambda-reference-architectures`의 기본값입니다.

- **CodeKeyPrefix** - `CodeBucket`과 관련된 Lambda 함수 코드의 키 접두사입니다. `file-processing`의 기본값입니다.

### 리소스
[The provided template](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)은
다음 리소스를 만듭니다.

- **InputBucket** - 원시 Markdown 파일이 저장된 S3 버킷입니다. 이 버킷에 파일을 업로드하면 두 처리 함수가 트리거됩니다.

- **OutputBucket** - 변형된 파일이 있는 프로세서 함수에 의해 채워지는 S3 버킷입니다.

- **InputNotificationTopic** - 각 객체 생성 알림에 대한 응답으로 여러 Lambda 함수를 호출하는 Amazon Simple Notification Service(Amazon SNS) 주제입니다.

- **NotificationPolicy** - `InputBucket`이 주제에 대한 `Publish` 작업을 호출할 수 있도록 허용하는 Amazon SNS 주제 정책입니다.

- **ProcessorFunctionOne** - Markdown 파일을 HTML로 변환하는 AWS Lambda 함수입니다. 이 함수의 배포 패키지가 `s3://[CodeBucket]/[CodeKeyPrefix]/data-processor-1.zip`에 있어야 합니다.

- **ProcessorFunctionTwo** - Markdown 파일을 일반 텍스트로 변환하는 AWS Lambda 함수입니다.  이 함수의 배포 패키지가 `s3://[CodeBucket]/[CodeKeyPrefix]/data-processor-2.zip`에 있어야 합니다.

- **LambdaExecutionRole** - 두 Lambda 함수에서 사용하는 AWS Identity and Access Management(IAM) 역할입니다.

- **RolePolicy** - **LambdaExecutionRole**과 연결된 IAM 정책이며 함수가 `InputBucket`으로부터 객체를 얻고, `OutputBucket`에 객체를 추가하고 Amazon CloudWatch에 로그를 기록할 수 있도록 허용합니다.

- **LambdaInvokePermissionOne** - Amazon SNS가 InputNotificationTopic의 알림을 기반으로 ProcessorFunctionOne을 호출할 수 있게 하는 정책입니다.

- **LambdaInvokePermissionTwo** - Amazon SNS가 InputNotificationTopic의 알림을 기반으로 ProcessorFunctionTwo를 호출할 수 있게 하는 정책입니다.


## 라이선스

이 레퍼런스 아키텍처 샘플은 Apache 2.0에서 라이선스가 부여되었습니다.
