#  Guidance for achieving near-zero RPO for applications using Amazon Aurora with Amazon RDS Proxy in a single region



This architecture diagram helps applications achieve near-zero Recovery Point Objective (RPO) leveraging Amazon Aurora with Amazon RDS Proxy. Amazon SQS provides a persistent message queue, ensuring data durability during potential Amazon Aurora failovers, minimizing data loss.



1. [Overview](#overview)
    - [Cost](#cost)
2. [Prerequisites](#prerequisites)
3. [Deployment Steps](#deployment-steps)
4. [Deployment Validation](#deployment-validation)
5. [Running the Guidance](#running-the-guidance)
6. [Next Steps](#next-steps)
7. [Cleanup](#cleanup)


## Overview

The guidance outlines a design pattern for applications that require a near-zero Recovery Point Objective (RPO), using Amazon Aurora and Amazon RDS Proxy. To prevent data loss during failover, data is stored in Amazon SQS.

Data loss, particularly during database failures, is a significant challenge for applications. Even with the use of highly available and fault-tolerant storage like Amazon Aurora, data loss can occur if the primary database instance fails. In such cases, Aurora automatically triggers a failover mechanism, rerouting requests to a secondary instance. This failover event can cause a brief interruption, during which read and write operations may fail, potentially leading to data loss. To mitigate this, data is temporarily persisted in an Amazon SQS and written to a database instance when available. The guide recommends using Amazon SQS to store data during failover, thereby reducing data loss.

![Architecture](/assets/Images/architecture.jpeg)

The solution is structured around two key applications: the ‘Demo App’ and the ‘Core App’. The ‘Demo App’  consists of user interface page to produce load for the application and log successful calls and errors in a simple UI. The ‘Core App’ is designed to temporarily store requests in Amazon SQS and consistently commit data to an Aurora instance, ensuring data availability before, during, and after any failover events. 

### Cost

This section is for a high-level cost estimate. Think of a likely straightforward scenario with reasonable assumptions based on the problem the Guidance is trying to solve. If applicable, provide an in-depth cost breakdown table in this section.

Start this section with the following boilerplate text:

The table below provides a sample cost breakdown for deploying this Guidance with the default parameters in the US East (N. Virginia) Region for one month. 

While the utlized services come with free tier usage, this breakdown assumes that the account into which you deploy this Guidance has no free tier usage remaining. Therefore, if the account into which you deploying this Guidance DOES have free tier usage remaining, your cost for running this Guidance should be less than what is estimated below.

| AWS Service  | Estimated Usage | Cost/Mo. [USD] |
| ----------- | ------------ | ------------ |
| Amazon API Gateway | ~3k REST API Calls per Demo Execution | $0.00
| Amazon CloudFront | < 50 HTTP Requests and < 1 GB Data Transfer Out | $0.08
| Amazon CloudWatch | 1 Dashboard and < 25 MB of Logs per Demo Execution | $3.00
| Amazon Cognito | 1 Monthly Active User | $0.00
| Amazon EventBridge | < 10 Events per Demo Execution | $0.00
| Amazon KMS | 1 CMK and < 10k Requests per Demo Execution | $1.03
| AWS Lambda | < 50 Lambda@Edge Invocations, < 4k 128 MB Requests per Demo Execution | $0.03
| Amazon S3 | < 5 MB of Standard Storage and ~100 GET/POST Requests per Deployment | $0.00
| AWS Secrets Manager | 2 Secrets per Deployment and ~3k API Calls per Demo Execution | $1.05
| Amazon SNS | ~3k Requests per Demo Execution | $0.01
| Amazon SQS | ~3k Standard Queue Requests per Demo Execution | $0.00
| Amazon RDS | 4 db.r6g.large Aurora Postgres Instances w/ RDS Proxies | $848.88
| AWS WAF | 1 ACL with 1 Common Bot Control Rule and ~3k Requests per Demo Execution | $6.00
| Amazon VPC | 1,464 NAT Gateway & Elastic IP hours | $73.20

_You are responsible for the cost of the AWS services used while running this Guidance. As of June 2024, the cost for running this Guidance with the default settings in the us-east-1 (N. Virginia) AWS Region is approximately $933.28/mo. or $1.27/hr._

## Prerequisites 

* Pick a unique-looking stack name (suggest all-caps with whole words describing what the stack does). These will become the prefix for all the resources the stack creates
* Pick a database username and password you'd like the demo to use for the Aurora databases it creates. Please be aware that the password must be longer than 8 characters and no special characters. The username can't be a Postgres keyword (like "admin")
* Provide a valid email address to receive a temporary password that you'll use to access the Demo app

## Deployment Steps

* See pre-requisites section above, as you will be prompted for these in the next step
* This solution can be deployed using a single main CloudFormation template located [here](/cfn). Both main.yml and main.json are functionally identical. This template takes roughly 30 minutes to deploy.
* During deployment, this template will launch several additional CloudFormation StackSets to fully deploy the required resources. While you don't need to launch or modify these StackSets directly, the underlying templates have been included in this repo for your reference.
* Once deployed, the primary stack you launch will contain the following outputs:
  * DemoDashboardUrl - The dashboard you'll use to simulate user traffic and failover
  * CloudWatchDashboardUrl - A CloudWwatch dashboard you can use to view application metrics
* An email will be sent to the email address provided during the CloudFormation stack setup, containing a temporary password. Use this temporary password to log into the DemoDashboard. Upon first login, the portal will prompt you to change the password.
  
## Deployment Validation 

The CloudFormation stack should not display any errors, and the output values should be available in the parent stack.

## Running the Guidance 

* Find the URL of demo dashboard: Go to CloudFormation -> Stacks -> The stack you just created -> Outputs “DemoDashboardUrl”
* Use the control panel in the top-left corner to run the test:
* Start with Step 1 : Generate Client Traffic. This step will generate simuated user  traffic

   ![Control Panel](/assets/Images/ControlPanel.png)
  
* Once the traffic is being generated , click Step 2 : Send Failover Request. This will initiate the database failover. Refer the sections on right side of the page 
  * Event Timeline : Status of failover request
  * Database roles : Roles of database before/after failover. The roles will swap  after failover.  
  * Queued records : Records persisted in queue and waiting to be commited to database 
  * Database Records Counts : Total records commited to database in each avaiability zone. Ideally, the count should remain the same after failover in both the instance of database
     
   ![Status](/assets/Images/Status.png)

* The application cloudwatch metrics can be accessed from the dashboard created by the stack deployment. Refer the output section of the parent stack for the URL. 

## Next Steps

The maxReceiveCount on the SQS’s redrive policy is set to 25. If the message in SQS is not processed after 25 attempts, it is sent to the Dead Letter Queue. The re-processing of the Dead Letter Queue is not included in this solution. However, the solution can be enhanced by implementing Dead Letter Queue processing.


## Cleanup 

* To clean up / undeploy this solution, simply delete the primary CloudFormation Stack you initially launched. The cleanup will take roughly 30 minutes
* When deleting the stack , some of the Lambda@Edge functions may end up in DELETE_FAILED state, with an error similar to below one:
    An error occurred (InvalidParameterValueException) when calling the DeleteFunction operation: Lambda was unable to delete arn:aws:lambda:us-east-1:12345:function:LambdaFunctionName:1 because it is a replicated function. 

   [refer to link for deleting Lambda@Edge Functions and Replicas.](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-edge-delete-replicas.html)

* In case you get the above error,  wait a few hours and try the delete of the nested stack again. It will work.

For any feedback, questions, or suggestions, please use the issues tab under this repo.

