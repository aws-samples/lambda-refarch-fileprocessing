# Serverlose Referenzarchitektur: Dateiverarbeitung in Echtzeit

Die Referenzarchitektur zur Dateiverarbeitung in Echtzeit ist eine ereignisgesteuerte Architektur zur parallelen Datenverarbeitung für allgemeine Zwecke, die [AWS Lambda](https://aws.amazon.com/lambda) verwendet. Die Architektur eignet sich optimal für Arbeitslasten, die mehr als eine Datenableitung eines Objekts benötigen. Diese einfache Architektur wird in diesem [Diagramm](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda-refarch-fileprocessing.pdf) und [im Blogpost "Fanout S3 Event Notifications to Multiple Endpoints"](https://aws.amazon.com/blogs/compute/fanout-s3-event-notifications-to-multiple-endpoints/) auf dem AWS Compute-Blog beschrieben. Diese Beispielanwendung zeigt eine Markdown-Konvertierungsanwendung in Fällen, in denen Lambda zur Markdown-Dateikonvertierung von HTML in Nur-Text verwendet wird.

## Ausführen der Beispielanwendung

Mithilfe der bereitgestellten [AWS CloudFormation-Vorlage](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template) können Sie einen Stapel starten, der die Referenzarchitektur für die Lambda-Dateiverarbeitung zeigt. Details über die mithilfe dieser Vorlage erstellen Ressourcen finden Sie im Abschnitt *Ressourcen der CloudFormation-Vorlage* in diesem Dokument.

**Wichtig** Da der AWS CloudFormation-Stapelname im Namen des Amazon Simple Storage Service (Amazon S3)-Buckets verwendet wird, darf dieser Stapelname nur aus Kleinbuchstaben bestehen. Verwenden Sie daher Kleinbuchstaben für den Stapelnamen. Die bereitgestellte CloudFormation-Vorlage ruft den Lambda-Code aus einem Bucket für die Region "us-east-1" ab. Um dieses Beispiel in einer anderen Region zu starten, ändern Sie die Vorlage und laden Sie den Lambda-Code in einen Bucket für diese Region hoch.


Wählen Sie **Launch Stack**, um die Vorlage für die Region "us-east-1" in Ihrem Konto zu starten:

[![Starten der Lambda-Dateiverarbeitung mit CloudFormation in Nord-Virginia](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/images/cloudformation-launch-stack-button.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=lambda-file-processing&amp;templateURL=https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)

Alternativ können Sie den Stapel mit dem folgenden Befehl und mithilfe von AWS CLI starten. Dies setzt jedoch voraus, dass Sie [die AWS CLI bereits installiert haben](http://docs.aws.amazon.com/cli/latest/userguide/installing.html).

```bash
aws cloudformation create-stack \
    --stack-name lambda-file-processing \
    --template-url https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template \
    --capabilities CAPABILITY_IAM
```

## Testen der Beispielanwendung

Nachdem Sie den Stapel mithilfe der CloudFormation-Vorlage erstellt haben, können Sie das System testen, indem Sie eine Markdown-Datei in den im Stapel erstellten "InputBucket" hochladen. Sie können die README.md-Datei im Repository als Beispieldatei verwenden. Nachdem die Datei hochgeladen wurde, können Sie die resultierenden HTML- und Nur-Text-Dateien im Ausgabe-Bucket des Stapels sehen. Sie können ebenfalls CloudWatch-Protokolle für die einzelnen Funktionen aufrufen, um Details zu ihrer Ausführung anzuzeigen.

Mithilfe der folgenden Befehle können Sie eine Beispieldatei vom bereitgestellten S3-Bucket in den Empfangs-Bucket des Stapels kopieren.

```
BUCKET=$(aws cloudformation describe-stack-resource --stack-name lambda-file-processing --logical-resource-id InputBucket --query "StackResourceDetail.PhysicalResourceId" --output text)
aws s3 cp s3://awslambda-reference-architectures/file-processing/example.md s3://$BUCKET/example.md
```

Nachdem die Datei in den Empfangs-Bucket hochgeladen wurde, können Sie den Ausgabe-Bucket überprüfen, um die gerenderten HTML- und Nur-Text-Ausgabedateien zu sehen, die von den Lambda-Funktionen erstellt wurden.

Ebenfalls können Sie die von den Lamda-Funktionen generierten CloudWatch-Protokolle aufrufen.

## Bereinigen der Beispielressourcen

Gehen Sie wie folgt vor, um alle in diesem Beispiel erstellten Ressourcen zu entfernen:

1. Löschen Sie alle Objekte in den Empfangs- und Ausgabe-Buckets.
1. Löschen Sie den CloudFormation-Stapel.
1. Löschen Sie die CloudWatch-Protokollgruppen, die die Ausführungsprotokolle der zwei Prozessorfunktionen enthalten.



## Ressourcen der CloudFormation-Vorlage

### Parameter
- **CodeBucket** – Name des S3-Buckets in der Region des Stapels, der den Code für die zwei Lambda-Funktionen, "ProcessorFunctionOne" und "ProcessorFunctionTwo", enthält. Verwendet standardmäßig den verwalteten Bucket "awslambda-reference-architectures".

- **CodeKeyPrefix** – Schlüsselpräfix für den Lambda-Funktionscode, der sich auf "CodeBucket" bezieht. Verwendet standardmäßig "file-processing".

### Ressourcen
[Die bereitgestellte Vorlage](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)
erstellt die folgenden Ressourcen:

- **InputBucket** – ein S3-Bucket, der die Markdown-Dateien mit den Rohdaten enthält. Das Hochladen einer Datei in diesen Bucket löst beide Verarbeitungsfunktionen aus.

- **OutputBucket** – ein S3-Bucket, den die Verarbeitungsfunktionen mit den transformierten Dateien auffüllen.

- **InputNotificationTopic** – ein Amazon Simple Notification Service (Amazon SNS)-Thema, das verwendet wird, um mehrere Lambda-Funktionen als Reaktion auf die einzelnen Objekterstellungsbenachrichtigungen aufzurufen.

- **NotificationPolicy** – eine Amazon SNS-Themenrichtlinie, die gestattet, dass "InputBucket" die Aktion "Veröffentlichen" für das Thema aufruft.

- **ProcessorFunctionOne** – eine AWS Lambda-Funktion, die Markdown-Dateien in HTML umwandelt. Das Bereitstellungspaket für diese Funktion muss sich unter "s3://[CodeBucket]/[CodeKeyPrefix]/data-processor-1.zip" befinden.

- **ProcessorFunctionTwo** – eine AWS Lambda-Funktion, die Markdown-Dateien in Nur-Text umwandelt.  Das Bereitstellungspaket für diese Funktion muss sich unter "s3://[CodeBucket]/[CodeKeyPrefix]/data-processor-2.zip" befinden.

- **LambdaExecutionRole** – eine AWS Identity and Access Management (IAM)-Rolle, die von den zwei Lambda-Funktionen verwendet wird.

- **RolePolicy** – eine mit **LambdaExecutionRole** verknüpfte IAM-Richtlinie, die ermöglicht, dass Funktionen Objekte aus "InputBucket" abrufen, Objekte in "OutputBucket" platzieren und Protokolle an Amazon CloudWatch ausgeben.

- **LambdaInvokePermissionOne** – eine Richtlinie, die es Amazon SNS ermöglicht, "ProcessorFunctionOne" basierend auf Benachrichtigungen von "InputNotificationTopic" aufzurufen.

- **LambdaInvokePermissionTwo** – eine Richtlinie, die es Amazon SNS ermöglicht, "ProcessorFunctionTwo" basierend auf Benachrichtigungen von "InputNotificationTopic" aufzurufen.


## Lizensierung

Dieses Beispiel einer Referenzarchitektur ist unter Apache 2.0 lizensiert.
