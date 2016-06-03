# Architecture de référence sans serveur : Traitement de fichier en temps réel

L'architecture de référence de traitement de fichier en temps réel est une architecture à visée générale de traitement de données en parallèle piloté par les événements qui utilise [AWS Lambda](https://aws.amazon.com/lambda). Cette architecture est idéale pour les charges de travail qui ont besoin de plusieurs dérivés de données d'un objet. Cette architecture simple est décrite dans ce [diagramme](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda-refarch-fileprocessing.pdf) et le [billet de blog « Fanout S3 Event Notifications to Multiple Endpoints »](https://aws.amazon.com/blogs/compute/fanout-s3-event-notifications-to-multiple-endpoints/) sur le blog de calcul AWS. Cet exemple d'application illustre une application de conversion Markdown dans laquelle Lambda est utilisé pour convertir des fichiers Markdown en HTML et en texte brut.

## Exécution de l'exemple

Vous pouvez utiliser le [template AWS CloudFormation](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template) fourni pour lancer une stack qui illustre l'architecture de référence de traitement de fichier Lambda. Vous trouverez des détails sur les ressources créées par ce template dans la section *Ressources de template CloudFormation* de ce document.

**Important** Comme le nom de stack AWS CloudFormation est utilisé dans le nom des buckets (compartiments) Amazon Simple Storage Service (Amazon S3), le nom de stack ne doit contenir que des lettres minuscules. Utilisez des lettres minuscules lorsque vous tapez le nom de stack. Le template CloudFormation fourni extrait son code Lambda d'un bucket dans la région us-east-1. Pour lancer cet exemple dans une autre région, veuillez modifier le template et charger le code Lambda dans un bucket de cette région.


Sélectionnez **Launch Stack** pour lancer le template dans la région us-east-1 dans votre compte :

[![Lancement de Lambda de traitement de fichier en Virginie du Nord) avec CloudFormation](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/images/cloudformation-launch-stack-button.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=lambda-file-processing&amp;templateURL=https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)

Sinon, vous pouvez utiliser la commande suivante pour lancer la stack à l'aide de l'interface de ligne de commande AWS CLI. Cela présume que vous avez déjà [installé AWS CLI](http://docs.aws.amazon.com/cli/latest/userguide/installing.html).

```bash
aws cloudformation create-stack \
    --stack-name lambda-file-processing \
    --template-url https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template \
    --capabilities CAPABILITY_IAM
```

## Test de l'exemple

Une fois que vous avez créé la stack à l'aide du template CloudFormation, vous pouvez tester le système en chargeant un fichier Markdown dans le bucket (compartiment) InputBucket créé dans la stack. Vous pouvez utiliser ce fichier README.md dans le référentiel comme exemple de fichier. Une fois que le fichier a été chargé, vous pouvez afficher les fichiers HTML et en texte brut dans le bucket de sortie de votre stack. Vous pouvez également afficher les journaux CloudWatch pour chacune des fonctions pour voir les détails de leur exécution.

Vous pouvez utiliser les commandes suivantes pour copier un exemple de fichier depuis le bucket (compartiment) S3 fourni vers le bucket d'entrée de votre stack.

```
BUCKET=$(aws cloudformation describe-stack-resource --stack-name lambda-file-processing --logical-resource-id InputBucket --query "StackResourceDetail.PhysicalResourceId" --output text)
aws s3 cp s3://awslambda-reference-architectures/file-processing/example.md s3://$BUCKET/example.md
```

Une fois que le fichier a été chargé dans le bucket (compartiment) d'entrée, vous pouvez inspecter le bucket de sortie pour afficher les fichiers HTML et en texte brut de sortie créés par les fonctions Lambda.

Vous pouvez également afficher les journaux CloudWatch générés par les fonctions Lambda.

## Nettoyage des ressources de l'exemple

Pour supprimer toutes les ressources créées par cet exemple, procédez comme suit :

1. Supprimez tous les objets des buckets (compartiments) d'entrée et de sorties.
1. Supprimez la stack CloudFormation.
1. Supprimez les groupes de journaux qui contiennent les journaux d'exécution pour les deux fonctions de traitement.



## Ressources du template CloudFormation

### Paramètres
- **CodeBucket** - Nom du bucket (compartiment) S3 dans la région de la stack qui contient le code des deux fonctions Lambda, ProcessorFunctionOne et ProcessorFunctionTwo. Par défaut, il s'agit du bucket opéré par `awslambda-reference-architectures`.

- **CodeKeyPrefix** - Le préfixe de clé pour le code de fonction Lambda relatif à `CodeBucket`. La valeur par défaut est `file-processing`.

### Ressources
[Le template fourni](https://s3.amazonaws.com/awslambda-reference-architectures/file-processing/lambda_file_processing.template)
crée les ressources suivantes :

- **InputBucket** - Un bucket (compartiment) S3 qui contient les fichiers Markdown bruts. Le chargement d'un fichier dans ce bucket déclenchera les deux fonctions de traitement.

- **OutputBucket** - Un bucket S3 alimenté par les fonctions de traitement avec les fichiers transformés.

- **InputNotificationTopic** - Une rubrique Amazon Simple Notification Service (Amazon SNS) utilisée pour appeler plusieurs fonctions Lambda en réponse à chaque notification de création d'objet.

- **NotificationPolicy** - Une politique de rubrique Amazon SNS qui autorise `InputBucket` à appeler l'action `Publish` sur la rubrique.

- **ProcessorFunctionOne** - Une fonction AWS Lambda qui convertit des fichiers Markdown en HTML. Le package de déploiement pour cette fonction doit être situé dans `s3://[CodeBucket]/[CodeKeyPrefix]/data-processor-1.zip`.

- **ProcessorFunctionTwo** - Une fonction AWS Lambda qui convertit des fichiers Markdown en texte brut.  Le package de déploiement pour cette fonction doit être situé dans `s3://[CodeBucket]/[CodeKeyPrefix]/data-processor-2.zip`.

- **LambdaExecutionRole** - Un rôle AWS Identity and Access Management (IAM) utilisé par les deux fonctions Lambda.

- **RolePolicy** - Une politique IAM associée à **LambdaExecutionRole** qui autorise les fonctions à extraire des objets de `InputBucket`, à les mettre dans `OutputBucket` et à se connecter à Amazon CloudWatch.

- **LambdaInvokePermissionOne** - Une politique qui permet à Amazon SNS d'appeler ProcessorFunctionOne en fonction de notifications d'InputNotificationTopic.

- **LambdaInvokePermissionTwo** - Une politique qui permet à Amazon SNS d'appeler ProcessorFunctionTwo en fonction de notifications d'InputNotificationTopic.


## Licence

Cet exemple d'architecture de référence est fourni sous licence sous Apache 2.0.
