# 无服务器参考架构：实时文件处理

实时文件处理参考架构是一个受事件驱动的通用并行数据处理架构，使用 [AWS Lambda](https://aws.amazon.com/lambda)。该架构非常适合需要某个对象的多种衍生数据的工作负载。此 [示意图](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda-refarch-fileprocessing.pdf) 以及 AWS 计算博客上的 ["Fanout S3 Event Notifications to Multiple Endpoints" blog post](https://aws.amazon.com/blogs/compute/fanout-s3-event-notifications-to-multiple-endpoints/) 中介绍了这个简单架构。这个示例应用程序演示了一个 Markdown 转换应用程序，该应用程序使用 Lambda 来将 Markdown 文件转换为 HTML 和纯文本。

## 运行示例

您可以使用提供的 [AWS CloudFormation 模板](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template) 启动一个堆栈，该堆栈演示了 Lambda 文件处理参考架构。在本文档的 *CloudFormation 模板资源* 部分中提供了有关通过该模板创建的资源的详细信息。

**重要提示** 由于 AWS CloudFormation 堆栈名称在 Amazon Simple Storage Service (Amazon S3) 存储桶的名称中使用，该堆栈名称只能包含小写字母。在键入堆栈名称时，使用小写字母。提供的 CloudFormation 模板会从 us-east-1 区域的存储桶中检索其 Lambda 代码。要在另一个区域中启动此示例，请修改模板并将 Lambda 代码上传到该区域的存储桶中。


选择 **Launch Stack** 以在您账户的 us-east-1 区域中启动模板：

[![使用 CloudFormation 在北弗吉尼亚区域中启动 Lambda 文件处理](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/images/cloudformation-launch-stack-button.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=lambda-file-processing&amp;templateURL=https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)

此外，您可以通过 AWS CLI 使用以下命令来启动堆栈。这假设您已 [安装 AWS CLI](http://docs.aws.amazon.com/cli/latest/userguide/installing.html)。

```bash
aws cloudformation create-stack \
    --stack-name lambda-file-processing \
    --template-url https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template \
    --capabilities CAPABILITY_IAM
```

## 测试示例

在您使用 CloudFormation 模板创建堆栈后，可以通过将 Markdown 文件上传到已在堆栈中创建的 InputBucket 来测试系统。您可以使用存储库中的此 README.md 文件作为示例文件。在上传该文件后，您可以在堆栈的输出存储桶中看到生成的 HTML 和纯文本文件。您还可以在 CloudWatch 日志中查看每个函数，以便了解函数执行的详细信息。

您可以使用下面的命令，将示例文件从提供的 S3 存储桶复制到您堆栈的输入存储桶中。

```
BUCKET=$(aws cloudformation describe-stack-resource --stack-name lambda-file-processing --logical-resource-id InputBucket --query "StackResourceDetail.PhysicalResourceId" --output text)
aws s3 cp s3://awslambda-reference-architectures/file-processing/example.md s3://$BUCKET/example.md
```

在将该文件上传到输入存储桶后，您可以检查输出存储桶，查看 Lambda 函数创建的 HTML 和纯文本格式的输出文件。

您还可以查看 Lambda 函数生成的 CloudWatch 日志。

## 清理示例资源

要删除此示例创建的所有资源，请执行以下操作：

1.删除输入和输出存储桶中的所有对象。
1.删除 CloudFormation 堆栈。
1.删除包含两个处理程序函数的执行日志的 CloudWatch 日志组。



## CloudFormation 模板资源

### 参数
- **CodeBucket** - 堆栈区域中的 S3 存储桶的名称，该区域包含两个 Lambda 函数 ProcessorFunctionOne 和 ProcessorFunctionTwo 的代码。默认为托管存储桶 `awslambda-reference-architectures`。

- **CodeKeyPrefix** - 与 `CodeBucket` 相关的 Lambda 函数代码的键前缀。默认为 `file-processing`。

### 资源
使用 [提供的模板](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)
可创建以下资源：

- **InputBucket** - 一个保存原始 Markdown 文件的 S3 存储桶。将文件上传到此存储桶时，将同时触发两个处理函数。

- **OutputBucket** - 一个 S3 存储桶，该存储桶由处理程序函数使用转换的文件填充。

- **InputNotificationTopic** - 一个 Amazon Simple Notification Service (Amazon SNS) 主题，该主题用于调用多个 Lambda 函数来响应各个对象创建通知。

- **NotificationPolicy** - 一个 Amazon SNS 主题策略，该策略允许 `InputBucket` 对主题调用 `Publish` 操作。

- **ProcessorFunctionOne** - 一个用于将 Markdown 文件转换为 HTML 的 AWS Lambda 函数。此函数的部署程序包必须位于 `s3://[CodeBucket]/[CodeKeyPrefix]/data-processor-1.zip` 中。

- **ProcessorFunctionTwo** - 一个用于将 Markdown 文件转换为纯文本的 AWS Lambda 函数。此函数的部署程序包必须位于 `s3://[CodeBucket]/[CodeKeyPrefix]/data-processor-2.zip` 中。

- **LambdaExecutionRole** - 一个 AWS Identity and Access Management (IAM) 角色，该角色由这两个 Lambda 函数使用。

- **RolePolicy** - 一个与 **LambdaExecutionRole** 关联的 IAM 策略，该策略允许函数从 `InputBucket` 获取对象，将对象置入 `OutputBucket`，并记录到 Amazon CloudWatch。

- **LambdaInvokePermissionOne** - 一个策略，该策略允许 Amazon SNS 根据来自 InputNotificationTopic 的通知调用 ProcessorFunctionOne。

- **LambdaInvokePermissionTwo** - 一个策略，该策略允许 Amazon SNS 根据来自 InputNotificationTopic 的通知调用 ProcessorFunctionTwo。


## 许可证

此示例参考架构已获得 Apache 2.0 许可。
