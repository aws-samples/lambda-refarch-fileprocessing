# Эталонная бессерверная архитектура: обработка файлов в реальном времени

Эталонная архитектура для обработки файлов в реальном времени – это универсальная архитектура параллельной обработки данных на основе событий, которая использует [AWS Lambda](https://aws.amazon.com/lambda). Она идеально подходит для рабочих нагрузок, для которых требуется несколько производных данных объекта. Эта простая архитектура описана на этой [схеме](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda-refarch-fileprocessing.pdf) и в ["Fanout S3 Event Notifications to Multiple Endpoints" blog post](https://aws.amazon.com/blogs/compute/fanout-s3-event-notifications-to-multiple-endpoints/) в блоге AWS Compute. В примере приложения Lambda используется для преобразования файлов Markdown в HTML и текст.

## Запуск примера

Вы можете использовать предоставленный [шаблон AWS CloudFormation](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template), чтобы запустить стек, демонстрирующий эталонную архитектуру для обработки файлов с помощью Lambda. Сведения о ресурсах, созданных этим шаблоном, представлены в разделе «Ресурсы шаблона CloudFormation» этого документа.

**Важно!** Так как имя стека AWS CloudFormation используется в имени корзин Amazon Simple Storage Service (Amazon S3), оно должно содержать только строчные буквы. При вводе имени стека используйте только строчные буквы. Предоставленный шаблон CloudFormation извлекает код Lambda из корзины в регионе us-east-1. Чтобы запустить пример в другом регионе, измените шаблон и загрузите код Lambda в корзину в этом регионе.


Выберите **Launch Stack**, чтобы запустить шаблон в регионе us-east-1 в вашем аккаунте:

[![Запуск обработки файлов Lambda в Северной Вирджинии с помощью CloudFormation](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/images/cloudformation-launch-stack-button.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=lambda-file-processing&amp;templateURL=https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)

Или же выполните следующую команду, чтобы запустить стек с помощью AWS CLI. При этом предполагается, что вы уже [установили AWS CLI](http://docs.aws.amazon.com/cli/latest/userguide/installing.html).

```bash
aws cloudformation create-stack \
    --stack-name lambda-file-processing \
    --template-url https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template \
    --capabilities CAPABILITY_IAM
```

## Тестирование примера

После создания стека с помощью шаблона CloudFormation вы можете проверить систему, загрузив файл Markdown в корзину InputBucket, созданную стеком. Для примера можно использовать файл README.md в этом репозитории. После передачи файла вы увидите полученные HTML-файл и текстовый файл в выходной корзине стека. Вы также можете просмотреть сведения о выполнении каждой функции в журналах CloudWatch.

Выполните следующие команды, чтобы скопировать пример файла из корзины S3 во входную корзину вашего стека.

```
BUCKET=$(aws cloudformation describe-stack-resource --stack-name lambda-file-processing --logical-resource-id InputBucket --query "StackResourceDetail.PhysicalResourceId" --output text)
aws s3 cp s3://awslambda-reference-architectures/file-processing/example.md s3://$BUCKET/example.md
```

После передачи файла во входную корзину вы можете просмотреть выходную корзину, где расположены полученные HTML-файл и текстовый файл, созданные функциями Lambda.

Вы также можете просмотреть журналы CloudWatch, созданные функциями Lambda.

## Очистка ресурсов примера

Чтобы удалить все ресурсы, созданные этим примером, выполните следующие действия.

1. Удалите все объекты во входной и выходной корзинах.
1. Удалите стек CloudFormation.
1. Удалите группы журналов CloudWatch, содержащие журналы выполнения двух функций обработки.



## Ресурсы шаблона CloudFormation

### Параметры
- **CodeBucket** – имя корзины S3 в регионе стека, содержащей код для двух функций Lambda: ProcessorFunctionOne и ProcessorFunctionTwo. По умолчанию используется управляемая корзина awslambda-reference-architectures.

- **CodeKeyPrefix** – префикс ключа для кода функции Lambda относительно CodeBucket. Значение по умолчанию: file-processing.

### Ресурсы
[Предоставленный шаблон](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)
создает следующие ресурсы.

- **InputBucket** – это корзина S3, в которой размещены файлы Markdown. При загрузке файла в эту корзину вызываются обе функции обработки.

- **OutputBucket** – в эту корзину S3 функции обработки добавляют преобразованные файлы.

- **InputNotificationTopic** – тема Amazon Simple Notification Service (Amazon SNS), используемая для вызова нескольких функций Lambda в ответ на каждое оповещение о создании объекта.

- **NotificationPolicy** – политика темы Amazon SNS, позволяющая InputBucket вызвать действие Publish для темы.

- **ProcessorFunctionOne** – эта функция AWS Lambda преобразует файлы Markdown в HTML. Пакет развертывания для нее должен быть расположен по следующему пути: s3://[CodeBucket]/[CodeKeyPrefix]/data-processor-1.zip.

- **ProcessorFunctionTwo** – эта функция AWS Lambda преобразует файлы Markdown в текстовые файлы.  Пакет развертывания для нее должен быть расположен по следующему пути: s3://[CodeBucket]/[CodeKeyPrefix]/data-processor-2.zip.

- **LambdaExecutionRole** – эту роль AWS Identity and Access Management (IAM) используют две функции Lambda.

- **RolePolicy** – политика IAM, связанная с ролью LambdaExecutionRole, которая позволяет функциям извлекать объекты из корзины InputBucket, добавлять объекты в корзину OutputBucket и вести журнал в Amazon CloudWatch.

- **LambdaInvokePermissionOne** – политика, позволяющая Amazon SNS вызывать функцию ProcessorFunctionOne в ответ на оповещения от InputNotificationTopic.

- **LambdaInvokePermissionTwo** – политика, позволяющая Amazon SNS вызывать функцию ProcessorFunctionTwo в ответ на оповещения от InputNotificationTopic.


## Лицензия

Данная эталонная архитектура лицензирована в соответствии с лицензией Apache 2.0.
