# Arquitetura de referência sem servidor: processamento de arquivos em tempo real

A arquitetura de referência de Processamento de arquivos em tempo real é uma arquitetura de processamento de uso geral, com base em evento e com dados paralelos que usa [AWS Lambda](https://aws.amazon.com/lambda). Esta arquitetura é ideal para cargas de trabalho que precisam de mais de um derivado de dados de um objeto. Esta arquitetura simples está descrita neste [diagrama](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda-refarch-fileprocessing.pdf) e em [postagem do blog "Fanout S3 Event Notifications to Multiple Endpoints"](https://aws.amazon.com/blogs/compute/fanout-s3-event-notifications-to-multiple-endpoints/) no Blog de computação da AWS. Esta aplicação da amostra demonstra uma aplicação de conversão Markdown em que o Lambda é usado para converter arquivos Markdown para HTML e texto sem formatação.

## Executando o exemplo

Você pode usar o [modelo AWS CloudFormation](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template) fornecido para iniciar uma pilha que demonstra a arquitetura de referência de processamento de arquivo Lambda. Os detalhes sobre os recursos criados por este modelo são fornecidos na seção *Recursos do modelo do CloudFormation* deste documento.

**Importante** Como o nome da pilha do AWS CloudFormation é usado no nome dos buckets Amazon Simple Storage Service (Amazon S3), o nome da pilha deve conter apenas letras minúsculas. Use letras minúsculas ao digitar o nome da pilha. O modelo do CloudFormation fornecido recupera seu código do Lambda de um bucket na região us-east-1. Para iniciar esta amostra em outra região, modifique o modelo e faça o upload do código do Lambda em um bucket nessa região.


Escolha **Launch Stack** para iniciar o modelo na região us-east-1 em sua conta:

[![Launch Lambda File Processing into North Virginia with CloudFormation](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/images/cloudformation-launch-stack-button.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=lambda-file-processing&amp;templateURL=https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)

Alternativamente, você pode usar o seguinte comando para iniciar a pilha usando o AWS CLI. Isso pressupõe que você já [instalou o AWS CLI](http://docs.aws.amazon.com/cli/latest/userguide/installing.html).

```bash
aws cloudformation create-stack \
    --stack-name lambda-file-processing \
    --template-url https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template \
    --capabilities CAPABILITY_IAM
```

## Testando o exemplo

Depois de ter criado a pilha usando o modelo CloudFormation, você pode testar o sistema de upload de um arquivo Markdown para o InputBucket que foi criado na pilha. Você pode usar esse arquivo README.md no repositório como um arquivo de exemplo. Depois que o arquivo foi carregado, você pode ver os arquivos HTML e os textos sem formatação resultantes do bucket de saída da pilha. Você também pode visualizar os registros de CloudWatch para cada uma das funções, a fim de ver os detalhes da sua execução.

Você pode usar os seguintes comandos para copiar um arquivo de amostra do bucket S3 fornecido dentro do bucket de entrada da sua pilha.

```
BUCKET=$(aws cloudformation describe-stack-resource --stack-name lambda-file-processing --logical-resource-id InputBucket --query "StackResourceDetail.PhysicalResourceId" --output text)
aws s3 cp s3://awslambda-reference-architectures/file-processing/example.md s3://$BUCKET/example.md
```

Depois que o arquivo foi carregado para o bucket de entrada, você pode inspecionar o bucket de saída para ver os arquivos de saída HTML e texto sem formatação criados pelas funções lambda.

Você também pode visualizar os registros do CloudWatch gerados pelas funções lambda.

## Limpando os recursos de exemplo

Para remover todos os recursos criados por este exemplo, faça o seguinte:

1. Exclua todos os objetos nos buckets de entrada e saída.
1. Exclua a pilha do CloudFormation.
1. Exclua os grupos de registro do CloudWatch que contêm os registros de execução para as duas funções de processador.



## Recursos do modelo do CloudFormation

### Parâmetros
- **CodeBucket** - Nome do bucket S3 na região da pilha que contém o código para as duas funções Lambda, ProcessorFunctionOne e ProcessorFunctionTwo. O padrão para o bucket gerenciado é "awslambda-reference-architectures".

- **CodeKeyPrefix** - O prefixo de chaves para o código da função Lambda em relação ao "CodeBucket". O padrão é "file-processing".

### Recursos
[O modelo fornecido](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)
cria os seguintes recursos:

- **InputBucket** - Um bucket S3 que contém os arquivos Markdown não processados. Fazer upload de um arquivo para este bucket irá desencadear ambas as funções de processamento.

- **OutputBucket** - Um bucket S3 que é preenchido pelas funções do processador com os arquivos transformados.

- **InputNotificationTopic** - Um tópico Amazon Simple Notification Service (Amazon SNS) usado para chamar múltiplas funções Lambda em resposta a cada notificação de criação do objeto.

- **NotificationPolicy** - Uma política de tópico Amazon SNS que permite "Input Bucket" para chamar a ação "Publish" sobre o tema.

- **ProcessorFunctionOne** - Uma função Lambda AWS que converte os arquivos Markdown para HTML. O pacote de implementação para esta função deve estar localizado em "s3://[CodeBucket]/[CodeKeyPrefix]/data-processor-1.zip".

- **ProcessorFunctionTwo** - Uma função Lambda da AWS que converte arquivos Markdown para texto sem formatação.  O pacote de implementação para esta função deve estar localizado em "s3://[CodeBucket]/[CodeKeyPrefix]/data-processor-2.zip".

- **LambdaExecutionRole** - Uma função AWS Identity and Access Management (IAM) usada pelas duas funções Lambda.

- **RolePolicy** - Uma política de IAM associada ao **LambdaExecutionRole** que permite às funções obter objetos do "InputBucket", colocar objeto para "OutputBucket" e registro para o Amazon CloudWatch.

- **LambdaInvokePermissionOne** - Uma política que permite ao Amazon SNS invocar ProcessorFunctionOne com base em notificações dos InputNotificationTopic.

- **LambdaInvokePermissionTwo** - Uma política que permite ao Amazon SNS invocar ProcessorFunctionTwo com base nas notificações do InputNotificationTopic.


## Licença

Este exemplo de arquitetura de referência é licenciado sob a licença do Apache 2.0.
