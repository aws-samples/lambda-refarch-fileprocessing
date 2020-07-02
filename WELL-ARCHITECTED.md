## Operational Excellence

#### OPS 1. How do you evaluate your Serverless application’s health?

* [ ] Question does not apply to this workload

* [x] **[Required]** Understand, analyze and alert on metrics provided out of the box
* [x] **[Best]** Use application, business, and operations metrics
* [x] **[Good]** Use distributed tracing and code is instrumented with additional context
* [ ] **[Good]** Use structured and centralized logging  
* [ ] None of these
  

##### Notes

>* The example uses structured logging output to Cloudwatch. For our example we only deploy to a single account so we don't require the use of cross account centralised logging.
>
>* We have alarms configured with notifications should processing fail.
>
>* We do not have a defined KPI within the application. We could however use a metric such as number of records processed within a given time frame and alert if this is outside of the defined thresholds.

---

#### OPS 2. How do you approach application lifecycle management?

* [ ] Question does not apply to this workload

* [x] **[Required]** Use infrastructure as code and stages isolated in separate environments
* [x] **[Good]** Prototype new features using temporary environments
* [ ] **[Good]** Use a rollout deployment mechanism
* [ ] **[Good]** Use configuration management
* [ ] **[Good]** Review the function runtime deprecation policy
* [ ] **[Best]** Use CI/CD including automated testing across separate accounts

* [ ] None of these


##### Notes

>* Our example utilizes infrastructure as code and includes a simple pipeline that will build and deploy within an individual account and to an individual environment. However the nature of this example means it can be deployed multiple times with different configurations. You can for example deploy a staging pipeline that would watch a development branch and deploy and changes to the Staging application stack. You could also deploy a production pipeline stack that watches the master branch and merges here will trigger a production release.
>
>* For this example a rollout mechanism would involve adopting either a Blue / Green deployment strategy with you controlling which input bucket a particular user hits . Alternatively for application business logic only changes these could be tested by having a notification invoke an alternate version of a lambda under specific conditions. 

---

## Security

#### SEC 1: How do you control access to your Serverless API?

* [x] Question does not apply to this workload


* [ ] **[Required]** Use appropriate endpoint type and mechanisms to secure access to your API
* [ ] **[Good]** Use authentication and authorization mechanisms
* [ ] **[Best]** Scope access based on identity’s metadata


* [ ] None of these


##### Notes

>This solution doesn't include an API frontend so the question doesn't apply.

---

#### SEC 2: How do you manage your Serverless application’s security boundaries?

* [ ] Question does not apply to this workload


* [x] **[Required]** Evaluate and define resource policies
* [x] **[Good]** Control network traffic at all layers
* [x] **[Best]** Smaller functions require fewer permissions
* [x] **[Required]** Use temporary credentials between resources and components

* [ ] None of these


##### Notes

> * We use IAM policy to ensure that resources can only be called by other resources that should be calling them.
>
> * All application components will assume a role with only the permissions it requires in order to perform its function. This will either be only being able to perform a specific action on multiple resources or any action on a particular resource. 
>
> * This application does not use private networking. 
>
> * We have individual functions for each different piece of business logic. 

---

#### SEC 3: How do you implement Application Security in your workload?***

* [ ] Question does not apply to this workload


* [x] **[Required]** Review security awareness documents frequently
* [x] **[Required]** Store secrets that are used in your code securely
* [ ] **[Good]** Implement runtime protection to help prevent against malicious code execution
* [ ] **[Best]** Automatically review workload’s code dependencies/libraries
* [x] **[Best]** Validate inbound events


* [ ] None of these


##### Notes

> * This application doesn't have any stored secrets. The GitHub token is required by CodePipeline, this is passed as a string for CloudFormation, it is not however visible within the CloudFormation console. This could be improved by manually creating a secrets manager entry for the token and replacing the CloudFormation parameter for the token with the secrets manager value by utilising Dynamic References.
>https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/dynamic-references.html
>
> * For reviewing dependencies and libraries we could integrate an automatic check into the pipeline. There are many tools and providers which can check code. Currently this is manual using PEP8 and Bandit manual checks. 
>
> * We only check for particular events and check to make sure the object is valid. 

---

## Reliability

#### REL 1. How do you regulate inbound request rates?

* [ ] Question does not apply to this workload


* [x] **[Required]** Use throttling to control inbound request rates
* [ ] **[Good]** Use, analyze and enforce API quotas
* [X] **[Best]** Use mechanisms to protect non-scalable resources


* [ ] None of these


##### Notes

> * We are using SQS queues in front of our Lambda functions, this helps us throttle the rate at which our application processes requests. 
>
> * We don't have API's to set quotas for.
>
> * Our downstream resources are S3 and DynamoDB on-demand which are more than capable of scaling to match our volumes.

---

#### REL 2. How do you build resiliency into your Serverless application?

* [ ] Question does not apply to this workload


* [x] **[Required]** Manage transaction, partial, and intermittent failures
* [x] **[Required]** Manage duplicate and unwanted events
* [ ] **[Good]** Orchestrate long-running transactions
* [x] **[Best]** Consider scaling patterns at burst rates


* [ ] None of these

##### Notes

> * We use SQS queues and DLQ's to ensure any processing failure results in a notification.
>
> * The Dynamo key and converted S3 object for each analysis is tied to the input object being analyzed. Pushing the same document will result in the same artifact.
>
> * Our example does not deal with duplicate files. Any duplicate will overwrite the previous, this could be improved inserting another layer of business logic that first checks the inbound file and renames with a UUID, it could additionally check to see if the file hash has already been processed. 
> 
> * The processing time of our transactions is fast and we can handle multiple files in a single invocation. Under heavy load of inbound files the SQS queue handles the work being distributed to lambda up to 1000 concurrent batches. 

---


## Performance Efficiency 

#### PERF 1. How do you optimize your Serverless application’s performance?

* [ ] Question does not apply to this workload


* [x] **[Required]** Measure, evaluate, and select optimum capacity units
* [x] **[Good]** Measure and optimize function startup time
* [ ] **[Good]** Take advantage of concurrency via async and stream-based function invocations
* [x] **[Good]** Optimize access patterns and apply caching where applicable
* [x] **[Best]** Integrate with managed services directly over functions when possible

* [ ] None of these


##### Notes

> * We have looked at how our function performs with different batch sizes and memory configurations to find what we believe is optimal for cost/performance .
>
> * For our example there is no real advantage to async. If concurrency was an issue it would be possible to chain the business logic, rather than perform it in parallel.
>
> * Data is pulled from S3 and held locally and cached for the execution, however currently there is only a single task performed per invocation so there is no benefit. Caching outside of the function would offer no benefit over S3.
>
> * In our Sentiment function we are utilising comprehend which a managed service. 

---

## Cost Optimization

#### COST 1. How do you optimize your Serverless application’s costs?

* [ ] Question does not apply to this workload

* [x] **[Required]** Minimize external calls and function code initialization
* [x] **[Required]** Optimize logging output and its retention
* [x] **[Good]** Optimize function configuration to reduce cost
* [x] **[Best]** Use cost-aware usage patterns in code

* [ ] None of these

##### Notes

>We have configurable logging levels and bench marked our function for optimal cost/performance.
