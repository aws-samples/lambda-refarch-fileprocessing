# Architettura di riferimento senza server: elaborazione dei file in tempo reale

L'architettura di riferimento per l'elaborazione dei file in tempo reale è un'architettura di elaborazione dati parallela, basata sugli eventi e destinata a scopi generici che utilizza [AWS Lambda](https://aws.amazon.com/lambda). Tale architettura è ideale per i carichi di lavoro che necessitano di più di un derivato dati di un oggetto. Questa architettura semplice è descritta in questo [diagramma](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda-refarch-fileprocessing.pdf) e nel [post "Fanout S3 Event Notifications to Multiple Endpoints"](https://aws.amazon.com/blogs/compute/fanout-s3-event-notifications-to-multiple-endpoints/) del blog AWS Compute. L'architettura esempio mostra un'applicazione di conversione Markdown in cui Lambda viene utilizzato per convertire file Markdown in HTML e testo semplice.

## Esecuzione dell'esempio

È possibile utilizzare il [modello AWS CloudFormation](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template) fornito, per avviare uno stack che mostra l'architettura di riferimento per l'elaborazione dei file Lambda. I dettagli sulle risorse create da questo modello sono disponibili nella sezione *CloudFormation Template Resources* di questo documento.

**Important** Poiché il nome dello stack di AWS CloudFormation è utilizzato nel nome dei bucket di Amazon Simple Storage Service (Amazon S3), il nome di tale stack deve contenere solo lettere minuscole. Utilizzare lettere minuscole durante la digitazione del nome dello stack. Il modello di CloudFormation fornito recupera il suo codice Lambda da un bucket nella regione Stati Uniti orientali 1. Per avviare questo esempio in un'altra regione, modificare il modello e caricare il codice Lambda in un bucket di quella regione.


Selezionare **Launch Stack** per avviare il modello nella regione Stati Uniti orientali 1 nell'account personale:

[![Launch Lambda File Processing into North Virginia with CloudFormation](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/images/cloudformation-launch-stack-button.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=lambda-file-processing&amp;templateURL=https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)

In alternativa, è possibile utilizzare il comando seguente per avviare lo stack tramite AWS CLI. Ciò presuppone l'[installazione di AWS CLI](http://docs.aws.amazon.com/cli/latest/userguide/installing.html).

```bash
aws cloudformation create-stack \
    --stack-name lambda-file-processing \
    --template-url https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template \
    --capabilities CAPABILITY_IAM
```

## Test dell'esempio

Dopo aver creato lo stack tramite il modello di CloudFormation, è possibile eseguire il test del sistema caricando un file Markdown nell'InputBucket creato nello stack. È possibile utilizzare il file README.md nel repository come file di esempio. Una volta caricato il file, è possibile visualizzare i risultanti file HTML e di testo semplice nel bucket di output dello stack. È possibile visualizzare anche i registri di CloudWatch di ciascuna funzione per vedere i dettagli della loro esecuzione.

È possibile utilizzare i comandi seguenti per copiare un file di esempio dal bucket S3 fornito nel bucket di input dello stack.

```
BUCKET=$(aws cloudformation describe-stack-resource --stack-name lambda-file-processing --logical-resource-id InputBucket --query "StackResourceDetail.PhysicalResourceId" --output text)
aws s3 cp s3://awslambda-reference-architectures/file-processing/example.md s3://$BUCKET/example.md
```

Una volta caricato il file nel bucket di input, è possibile ispezionare il bucket di output per vedere la resa dei file di output HTML e di testo semplice creati dalle funzioni di Lambda.

È possibile visualizzare anche i registri di CloudWatch generati dalle funzioni di Lambda.

## Eliminazione delle risorse dell'esempio

Per eliminare tutte le risorse create da questo esempio, effettuare i seguenti passaggi:

1. Eliminare tutti gli oggetti nei bucket di input e output.
1. Eliminare lo stack di CloudFormation.
1. Eliminare i gruppi di registro di CloudWatch che contengono i registri di esecuzione per le due funzioni del processore.



## Risorse dei modelli di CloudFormation

### Parametri
- **CodeBucket**: nome del bucket S3 nella regione dello stack che contiene il codice per le due funzioni di Lambda, ProcessorFunctionOne e ProcessorFunctionTwo. Impostazioni predefinite sul bucket gestito "awslambda-reference-architectures".

- **CodeKeyPrefix**: prefisso della chiave per il codice delle funzioni di Lambda relativo a "CodeBucket". Impostazioni predefinite su "file-processing".

### Risorse
[Il modello fornito](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)
crea le risorse seguenti:

- **InputBucket**: bucket S3 che contiene i file Markdown non elaborati. Il caricamento di un file in questo bucket attiva entrambe le funzioni di elaborazione.

- **OutputBucket**: bucket S3 popolato dalle funzioni del processore con i file trasformati.

- **InputNotificationTopic**: argomento di Amazon Simple Notification Service (Amazon SNS) utilizzato per richiamare più funzioni di Lambda in risposta alla notifica della creazione di ciascun oggetto.

- **NotificationPolicy**: policy dell'argomento di Amazon SNS che permette a "InputBucket" di richiedere l'azione "Publish" all'argomento.

- **ProcessorFunctionOne**: funzione di AWS Lambda che converte i file Markdown in HTML. Il pacchetto di distribuzione per questa funzione deve essere collocato in "s3://[CodeBucket]/[CodeKeyPrefix]/data-processor-1.zip".

- **ProcessorFunctionTwo**: funzione di AWS Lambda che converte i file Markdown in testo semplice.  Il pacchetto di distribuzione per questa funzione deve essere collocato in "s3://[CodeBucket]/[CodeKeyPrefix]/data-processor-2.zip".

- **LambdaExecutionRole**: ruolo di AWS Identity and Access Management (IAM) utilizzato dalle due funzioni di Lambda.

- **RolePolicy**: policy di IAM associata a **LambdaExecutionRole** che consente alle funzioni di prendere oggetti da "InputBucket", posizionare oggetti in "OutputBucket" e accedere ad Amazon CloudWatch.

- **LambdaInvokePermissionOne**: policy che consente ad Amazon SNS di richiamare ProcessorFunctionOne in base alle notifiche di InputNotificationTopic.

- **LambdaInvokePermissionTwo**: policy che consente ad Amazon SNS di richiamare ProcessorFunctionTwo in base alle notifiche di InputNotificationTopic.


## Licenza

La licenza di questo esempio di architettura di riferimento è fornita con Apache 2.0.
