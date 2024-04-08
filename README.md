#  Guidance for achieving near-zero RPO for applications using Amazon Aurora with Amazon RDS Proxy in a single region



This architecture diagram helps applications achieve near-zero Recovery Point Objective (RPO) leveraging Amazon Aurora with Amazon RDS Proxy. Amazon SQS provides a persistent message queue, ensuring data durability during potential Amazon Aurora failovers, minimizing data loss.



1. [Overview](#overview-required)
    - [Cost](#cost)
2. [Prerequisites](#prerequisites-required)
    - [Operating System](#operating-system-required)
3. [Deployment Steps](#deployment-steps-required)
4. [Deployment Validation](#deployment-validation-required)
5. [Running the Guidance](#running-the-guidance-required)
6. [Next Steps](#next-steps-required)
7. [Cleanup](#cleanup-required)
8. [Authors](#authors-optional)

## Overview 

The guidance outlines a design pattern for applications that require a near-zero Recovery Point Objective (RPO), using Amazon Aurora and Amazon RDS Proxy. To prevent data loss during failover, data is stored in Amazon SQS.

Data loss, particularly during database failures, is a significant challenge for applications. Even with the use of highly available and fault-tolerant storage like Amazon Aurora, data loss can occur if the primary database instance fails. In such cases, Aurora automatically triggers a failover mechanism, rerouting requests to a secondary instance. This failover event can cause a brief interruption, during which read and write operations may fail, potentially leading to data loss. To mitigate this, data is temporarily persisted in an Amazon SQS and written to a database instance when available. The guide recommends using Amazon SQS to store data during failover, thereby reducing data loss.

![Architecture](/assets/Images/architecture.jpeg)

The solution is structured around two key applications: the ‘Demo App’ and the ‘Core App’. The ‘Demo App’  consists of user interface page to produce load for the application and log successful calls and errors in a simple UI. The ‘Core App’ is designed to temporarily store requests in Amazon SQS and consistently commit data to an Aurora instance, ensuring data availability before, during, and after any failover events. 


### Cost

This section is for a high-level cost estimate. Think of a likely straightforward scenario with reasonable assumptions based on the problem the Guidance is trying to solve. If applicable, provide an in-depth cost breakdown table in this section.

Start this section with the following boilerplate text:

_You are responsible for the cost of the AWS services used while running this Guidance. As of <month> <year>, the cost for running this Guidance with the default settings in the <Default AWS Region (Most likely will be US East (N. Virginia)) > is approximately $<n.nn> per month for processing ( <nnnnn> records )._

Replace this amount with the approximate cost for running your Guidance in the default Region. This estimate should be per month and for processing/serving resonable number of requests/entities.


## Prerequisites 

* Pick a unique-looking stack name (suggest all-caps with whole words describing what the stack does). These will become the prefix for all the resources the stack creates
* Pick a database username and password you'd like the demo to use for the Aurora databases it creates. Please be aware that the password must be longer than 8 characters and no special characters
* Provide a valid email ID to receive temporary password for the Demo app 

## Deployment Steps

* See pre-requisites section above, as you will be prompted for these by the next step
* This solution can be deployed using a single main CloudFormation template located [here](/cfn). Both main.yml and main.json are functionally identical. This template takes roughly 30 minutes to deploy.
* During deployment, this template will launch several additional CloudFormation StackSets to fully deploy the required resources. While you don't need to launch or modify these StackSets directly, the underlying templates have been included in this repo for your reference
* Once deployed, the primary stack you launch will contain the following outputs:
  * CloudWatchDashboardUrl - Cloudwatch Dashbaord to access application metrics
  * DemoDashboardUrl - The dashbaord to simulate user traffic and failover
* An email will be sent to the email ID provided during the CloudFormation stack setup, containing a temporary password. Use this temporary password to log in to the DemoDashboard. Upon first login, the portal will prompt you to change the password.
  
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

## Next Steps

The maxReceiveCount on the SQS’s redrive policy is set to 25. If the message in SQS is not processed after 25 attempts, it is sent to the Dead Letter Queue. The re-processing of the Dead Letter Queue is not included in this solution. However, the solution can be enhanced by implementing Dead Letter Queue processing.


## Cleanup (required)

* To clean up / undeploy this solution, simply delete the primary CloudFormation Stack you initially launched. The cleanup will take roughly 30 minutes
* If you see a delete failure, retry it, without skipping any failed deletions


For any feedback, questions, or suggestions, please use the issues tab under this repo.

