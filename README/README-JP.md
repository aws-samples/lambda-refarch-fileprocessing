# サーバーレスリファレンスアーキテクチャ: リアルタイムのファイル処理

リアルタイムのファイル処理リファレンスアーキテクチャは、[AWS Lambda](https://aws.amazon.com/lambda) を使用する、汎用でイベント駆動型の並列データ処理アーキテクチャです。このアーキテクチャは、オブジェクトの複数のデータ派生物を必要とするワークロードに最適です。このシンプルなアーキテクチャについては、この [図](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda-refarch-fileprocessing.pdf) および AWS コンピューティングブログの ["Fanout S3 Event Notifications to Multiple Endpoints" ブログの投稿](https://aws.amazon.com/blogs/compute/fanout-s3-event-notifications-to-multiple-endpoints/) で説明しています。このサンプルアプリケーションは、Markdown ファイルを HTML とプレーンテキストに変換するために Lambda を使用する Markdown 変換アプリケーションを示しています。

## 例の実行

用意された [AWS CloudFormation テンプレート](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template) を使用して、Lambda ファイル処理のリファレンスアーキテクチャを示すスタックを起動できます。このテンプレートで作成されるリソースの詳細は、このドキュメントの「*CloudFormation テンプレートのリソース*」セクションで説明しています。

**重要** AWS CloudFormation スタック名が Amazon Simple Storage Service (Amazon S3) バケット名で使用されるため、そのスタック名には小文字のみを含める必要があります。スタック名を入力するときは小文字を使用してください。用意された CloudFormation テンプレートは、us-east-1 region リージョンのバケットからその Lambda コードを取得します。別のリージョンでこのサンプルを起動するには、テンプレートを変更し、そのリージョンのバケットに Lambda コードをアップロードします。


[**Launch Stack**] を選択して、アカウントで us-east-1 リージョンにテンプレートを起動します。

[![CloudFormation を使用して Lambda ファイル処理を北バージニアに起動する](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/images/cloudformation-launch-stack-button.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=lambda-file-processing&amp;templateURL=https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)

代わりに、次のコマンドで、AWS CLI を使用してスタックを起動できます。この例では、すでに [AWS CLI をインストール済み](http://docs.aws.amazon.com/cli/latest/userguide/installing.html) であることを前提としています。

```bash
aws cloudformation create-stack \
    --stack-name lambda-file-processing \
    --template-url https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template \
    --capabilities CAPABILITY_IAM
```

## 例のテスト

CloudFormation テンプレートを使用してスタックを作成したら、スタックで作成された InputBucket に Markdown ファイルをアップロードしてシステムをテストできます。レポジトリ内のこの README.md ファイルは、サンプルファイルとして使用できます。ファイルがアップロードされたら、生成される HTML とプレーンテキストファイルをスタックの出力バケットで表示できます。各関数の CloudWatch ログを表示して、実行の詳細を確認することもできます。

次のコマンドを使用して、用意された S3 バケットからスタックの入力バケットにサンプルファイルをコピーすることができます。

```
BUCKET=$(aws cloudformation describe-stack-resource --stack-name lambda-file-processing --logical-resource-id InputBucket --query "StackResourceDetail.PhysicalResourceId" --output text)
aws s3 cp s3://awslambda-reference-architectures/file-processing/example.md s3://$BUCKET/example.md
```

ファイルが入力バケットにアップロードされたら、出力バケットを検査し、Lambda 関数によって作成され、レンダリングされた HTML およびプレーンテキスト出力ファイルを表示できます。

Lambda 関数によって生成された CloudWatch ログを表示することもできます。

## リソース例のクリーンアップ

この例で作成されたすべてのリソースを削除するには、次の操作を行います。

1.入出力バケットのすべてのオブジェクトを削除します。
1.CloudFormation スタックを削除します。
1.2 つのプロセッサ関数の実行ログを含む CloudWatch ロググループを削除します。



## CloudFormation テンプレートのリソース

### パラメーター
- **CodeBucket** - 2 つの Lambda 関数 (ProcessorFunctionOne および ProcessorFunctionTwo) のコードを含む、スタックのリージョンの S3 バケットの名前。デフォルトはマネージドバケット `awslambda-reference-architectures` です。

- **CodeKeyPrefix** - `CodeBucket` に相対的な Lambda 関数コードのキープレフィックス。デフォルトは `file-processing` です。

### リソース
[用意されたテンプレート](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)
 では以下のリソースが作成されます。

- **InputBucket** - Markdown の raw ファイルを保持する S3 バケット。このバケットにファイルをアップロードすると、両方の処理関数がトリガーされます。

- **OutputBucket** - プロセッサ関数によって、変換されたファイルが入力される S3 バケット。

- **InputNotificationTopic** - 各オブジェクトの作成通知に応答して複数の Lambda 関数を呼び出すために使用される Amazon Simple Notification Service (Amazon SNS) トピック。

- **NotificationPolicy** - トピックで `Publish` アクションを呼び出す `InputBucket` を許可する Amazon SNS トピックポリシー。

- **ProcessorFunctionOne** - Markdown ファイルを HTML に変換する AWS Lambda 関数。この関数のデプロイパッケージは `s3://[CodeBucket]/[CodeKeyPrefix]/data-processor-1.zip` にあります。

- **ProcessorFunctionTwo** - Markdown ファイルをプレーンテキストに変換する AWS Lambda 関数。この関数のデプロイパッケージは `s3://[CodeBucket]/[CodeKeyPrefix]/data-processor-2.zip` にあります。

- **LambdaExecutionRole** - 2 つの Lambda 関数によって使用される AWS Identity and Access Management (IAM) ロール。

- **RolePolicy** - 関数が `InputBucket` からオブジェクトを取得し、オブジェクトを `OutputBucket` に配置して、Amazon CloudWatch に記録できるようにする **LambdaExecutionRole** に関連付けられた IAM ポリシー。

- **LambdaInvokePermissionOne** - Amazon SNS が InputNotificationTopic からの通知に基づいて ProcessorFunctionOne を呼び出せるようにするポリシー。

- **LambdaInvokePermissionTwo** - Amazon SNS が InputNotificationTopic からの通知に基づいて ProcessorFunctionTwo を呼び出せるようにするポリシー。


## ライセンス

このリファレンスアーキテクチャサンプルは Apache 2.0 でライセンスされています。
