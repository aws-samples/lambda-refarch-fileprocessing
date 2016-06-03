# 無伺服器參考架構：即時檔案處理

即時檔案處理參考架構是利用 [AWS Lambda](https://aws.amazon.com/lambda) 運作的一般用途、事件驅動的平行資料處理架構。此架構很適合需要一個以上的物件資料衍生物的工作負載。在 [示意圖](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda-refarch-fileprocessing.pdf) 與 AWS 運算部落格的 ["Fanout S3 Event Notifications to Multiple Endpoints" 部落格文章](https://aws.amazon.com/blogs/compute/fanout-s3-event-notifications-to-multiple-endpoints/) 中，有關於此簡易架構的說明。此簡易的應用程式示範 Markdown 轉換應用程式，Lambda 使用此應用程式將 Markdown 檔案轉換為 HTML 與純文字。

## 執行範例

您可以使用系統提供的 [AWS CloudFormation 範本](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template) 啟動示範 Lambda 檔案處理參考架構的堆疊。本文件的 *CloudFormation 範本資源* 章節中有提供關於此範例所建立資源的詳細資訊。

**重要** 由於 AWS CloudFormation 堆疊名稱將使用於 Amazon Simple Storage Service (Amazon S3) 儲存貯體的名稱，因此堆疊名稱只能包含小寫字母。輸入堆疊名稱時，請使用小寫字母。系統提供的 CloudFormation 範本會從 us-east-1 區域的儲存貯體取回其 Lambda 程式碼。若要在其他區域啟動此範例，請修改範本並將 Lambda 程式碼上傳至該區域的儲存貯體。


選擇 **Launch Stack** 以啟動您帳戶的 us-east-1 區域中的範本。

[![Launch Lambda File Processing into North Virginia with CloudFormation](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/images/cloudformation-launch-stack-button.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=lambda-file-processing&amp;templateURL=https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)

或者，您可以使用以下命令啟動堆疊以使用 AWS CLI。這裡假設您已 [安裝 AWS CLI](http://docs.aws.amazon.com/cli/latest/userguide/installing.html)。

```bash
aws cloudformation create-stack \
    --stack-name lambda-file-processing \
    --template-url https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template \
    --capabilities CAPABILITY_IAM
```

## 測試範例

在您使用 CloudFormation 範本建立堆疊之後，可藉由將 Markdown 檔案上傳至於堆疊中建立的 InputBucket 以測試系統。您可以使用儲存庫中的 README.md 檔案做為範例檔案。在檔案上傳之後，可在您的堆疊的輸出儲存貯體中看到結果的 HTML 與純文字檔案。您亦可檢視各項功能的 CloudWatch 記錄以查看其執行的詳細資訊。

您可以使用以下命令，將範例檔案從系統提供的 S3 儲存貯體複製至您的堆疊的輸入儲存貯體。

```
BUCKET=$(aws cloudformation describe-stack-resource --stack-name lambda-file-processing --logical-resource-id InputBucket --query "StackResourceDetail.PhysicalResourceId" --output text)
aws s3 cp s3://awslambda-reference-architectures/file-processing/example.md s3://$BUCKET/example.md
```

在檔案上傳至輸入儲存貯體之後，您可以檢查輸出儲存貯體以查看經過 Lambda 功能處理的 HTML 與純文字輸出檔案。

您亦可檢視由 Lambda 功能產生的 CloudWatch 記錄。

## 清除應用範例資源

若要移除此範例建立的所有資源，請執行以下動作：

1.刪除輸入與輸出儲存貯體中的所有物件。
1.刪除 CloudFormation 堆疊。
1.刪除包含兩個處理器功能的執行記錄的 CloudWatch 記錄群組。



## CloudFormation 範本資源

### 參數
- **CodeBucket** - 包含兩個 Lambda 功能 ProcessorFunctionOne 與 ProcessorFunctionTwo 的堆疊區域中的 S3 儲存貯體的名稱。預設為受管儲存貯體「awslambda-reference-architectures」。

- **CodeKeyPrefix** - 與「CodeBucket」相關的 Lambda 功能程式碼的金鑰前綴。預設為「file-processing」。

### 資源
[系統提供的範本](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)
建立以下資源：

- **InputBucket** - 存放原始 Markdown 檔案的 S3 儲存貯體。上傳檔案至此儲存貯體將觸發兩個處理功能。

- **OutputBucket** - 由處理器功能與轉換後的檔案所填入的 S3 儲存貯體。

- **InputNotificationTopic** - 用於呼叫多個 Lambda 功能以回應各個物件建立通知的 Amazon Simple Notification Service (Amazon SNS) 主題。

- **NotificationPolicy** - 允許「InputBucket」呼叫主題上的「Publish」動作的 Amazon SNS 主題政策。

- **ProcessorFunctionOne** - 可將 Markdown 檔案轉換為 HTML 的 AWS Lambda 功能。此功能的部署套件必須位於「s3://[CodeBucket]/[CodeKeyPrefix]/data-processor-1.zip」。

- **ProcessorFunctionTwo** - 可將 Markdown 檔案轉換為純文字的 AWS Lambda 功能。此功能的部署套件必須位於「s3://[CodeBucket]/[CodeKeyPrefix]/data-processor-2.zip」。

- **LambdaExecutionRole** - 由兩個 Lambda 功能使用的 AWS Identity and Access Management (IAM) 角色。

- **RolePolicy** - 與 **LambdaExecutionRole** 關聯的 IAM 政策，它允許功能從「InputBucket」取得物件、將物件放入「OutputBucket」，以及記錄至 Amazon CloudWatch。

- **LambdaInvokePermissionOne** - 可讓 Amazon SNS 依據來自 InputNotificationTopic 的通知以呼叫 ProcessorFunctionOne 的一個政策。

- **LambdaInvokePermissionTwo** - 可讓 Amazon SNS 依據來自 InputNotificationTopic 的通知以呼叫 ProcessorFunctionTwo 的一個政策。


## 授權

此參考架構範例依據 Apache 2.0 授權。
