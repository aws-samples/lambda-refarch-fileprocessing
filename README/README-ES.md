# Arquitectura de referencia sin servidor: Procesamiento de archivos en tiempo real

La arquitectura de referencia Procesamiento de archivos en tiempo real es una arquitectura de procesamiento de datos en paralelo controlada por eventos de propósito general que usa [AWS Lambda](https://aws.amazon.com/lambda). Esta arquitectura es ideal para cargas de trabajo que necesitan obtener más de un dato de un objeto. Esta arquitectura sencilla se describe en este [diagrama](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda-refarch-fileprocessing.pdf) y en la [entrada de blog "Fanout S3 Event Notifications to Multiple Endpoints"](https://aws.amazon.com/blogs/compute/fanout-s3-event-notifications-to-multiple-endpoints/) del blog AWS Compute. Esta aplicación de ejemplo muestra una aplicación de conversión de Markdown en la que se utiliza Lambda para convertir archivos Markdown en HTML y texto sin formato.

## Ejecución del ejemplo

Puede usar la [plantilla de AWS CloudFormation](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template) proporcionada para lanzar una pila que muestre la arquitectura de referencia de procesamiento de archivos con Lambda. En la sección *Recursos de la plantilla de CloudFormation* de este documento encontrará información detallada sobre los recursos creados por esta plantilla.

**Importante** Como el nombre de la pila de AWS CloudFormation se usa en el nombre de los buckets de Amazon Simple Storage Service (Amazon S3), ese nombre de pila solo debe contener letras en minúscula. Use letras en minúscula cuando escriba el nombre de la pila. La plantilla de CloudFormation proporcionada recupera su código Lambda de un bucket de la región us-east-1. Para ejecutar este ejemplo en otra región, modifique la plantilla y cargue el código Lambda en un bucket de esa región.


Elija **Launch Stack** para lanzar la plantilla en la región us-east-1 de su cuenta:

[![Launch Lambda File Processing into North Virginia with CloudFormation](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/images/cloudformation-launch-stack-button.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=lambda-file-processing&amp;templateURL=https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)

También puede usar el siguiente comando para lanzar la pila mediante el CLI de AWS. Se presupone que ya ha [instalado AWS CLI](http://docs.aws.amazon.com/cli/latest/userguide/installing.html).

```bash
aws cloudformation create-stack \
    --stack-name lambda-file-processing \
    --template-url https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template \
    --capabilities CAPABILITY_IAM
```

## Probar el ejemplo

Una vez creada la pila mediante la plantilla de CloudFormation, puede probar el sistema cargando un archivo Markdown en el InputBucket que se creó en la pila. Puede usar este archivo README.md del repositorio como archivo de ejemplo. Después de cargar el archivo, puede ver los archivos HTML y de texto sin formato resultantes en el bucket de salida de la pila. También puede ver los logs de CloudWatch de cada una de las funciones si desea obtener información detallada de la ejecución.

Puede usar los siguientes comandos para copiar un archivo de ejemplo del bucket de S3 proporcionado en el bucket de entrada de la pila.

```
BUCKET=$(aws cloudformation describe-stack-resource --stack-name lambda-file-processing --logical-resource-id InputBucket --query "StackResourceDetail.PhysicalResourceId" --output text)
aws s3 cp s3://awslambda-reference-architectures/file-processing/example.md s3://$BUCKET/example.md
```

Después de cargar el archivo en el bucket de entrada, puede examinar el bucket de salida para ver los archivos de salida HTML y de texto sin formato resultantes creados por las funciones Lambda.

También puede ver los logs de CloudWatch generados por las funciones Lambda.

## Borrado de los recursos del ejemplo

Para eliminar todos los recursos creados por este ejemplo, proceda del modo siguiente:

1. Elimine todos los objetos de los buckets de entrada y salida.
1. Elimine la pila de CloudFormation.
1. Elimine los grupos de logs de CloudWatch que contienen los logs de ejecución de las dos funciones de procesamiento.



## Recursos de la plantilla de CloudFormation

### Parámetros
- **CodeBucket**: nombre del bucket de S3 de la región de la pila que contiene el código de las dos funciones Lambda, ProcessorFunctionOne y ProcessorFunctionTwo. Está establecido de forma predeterminada en el bucket administrado `awslambda-reference-architectures`.

- **CodeKeyPrefix**: el prefijo de clave del código de la función Lambda correspondiente a `CodeBucket`. De forma predeterminada es `file-processing`.

### Recursos
[La plantilla proporcionada](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)
crea los recursos siguientes:

- **InputBucket**: un bucket de S3 que almacena los archivos Markdown sin formato. Al cargar un archivo en este bucket se desencadenarán ambas funciones de procesamiento.

- **OutputBucket**: un bucket de S3 que rellenan las funciones de procesamiento con los archivos convertidos.

- **InputNotificationTopic**: un tema de Amazon Simple Notification Service (Amazon SNS) usado para invocar a varias funciones Lambda en respuesta a cada notificación de creación de un objeto.

- **NotificationPolicy**: una política de tema de Amazon SNS que permite a `InputBucket` llamar a la acción `Publish` en el tema.

- **ProcessorFunctionOne**: una función de AWS Lambda que convierte archivos Markdown en HTML. El paquete de implementación de esta función debe estar ubicado en `s3://[CodeBucket]/[CodeKeyPrefix]/data-processor-1.zip`.

- **ProcessorFunctionTwo**: una función de AWS Lambda que convierte archivos Markdown en texto sin formato.  El paquete de implementación de esta función debe estar ubicado en `s3://[CodeBucket]/[CodeKeyPrefix]/data-processor-2.zip`.

- **LambdaExecutionRole**: un rol de AWS Identity and Access Management (IAM) usado por las dos funciones Lambda.

- **RolePolicy**: una política de IAM asociada a **LambdaExecutionRole** que permite que las funciones obtengan objetos de `InputBucket`, coloquen objetos en `OutputBucket` y creen un log en Amazon CloudWatch.

- **LambdaInvokePermissionOne**: una política que permite a Amazon SNS invocar a ProcessorFunctionOne a partir de las notificaciones de InputNotificationTopic.

- **LambdaInvokePermissionTwo**: una política que permite a Amazon SNS invocar a ProcessorFunctionTwo a partir de las notificaciones de InputNotificationTopic.


## Licencia

Este ejemplo de arquitectura de referencia tiene licencia de Apache 2.0.
