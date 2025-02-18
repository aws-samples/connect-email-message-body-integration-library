## Prerequisites

You must have the following prerequisites:

- An [AWS account](https://signin.aws.amazon.com/signin)
- The [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
- Python 3.11 or later
- AWS CDK
- An Amazon Connect Instance with Email for Amazon Connect enabled
- If you don’t already have the AWS CLI on your local machine, refer to Installing or updating the latest version of the AWS 
CLI and Configuring the AWS CLI.

Install the AWS CDK Toolkit globally using the following node package manager command:
- npm install -g aws-cdk-lib@latest

### Guidance for completing .env file
You must have the following pieces of information in order to fill in the required values:
- The bucket name associated to your Amazon Connect Instance
- The instance name associated to your Amazon Connect Instance
- The instance arn associated to your Amazon Connect Instance
    - go to the Amazon Connect in the AWS console
    - select the instance alias you want to use for this solution
    - copy and paste the arn
- The hours of service arn associated to your Amazon Connect Instance found in the hours of operation in your instance
    - select the hours of opperation you want to associate to the queues
    - select Show additional hours of operation information and copy and paste the arn

#### Setup a virtual environment

This project is set up like a standard Python project. Create a Python virtual environment using the following code:

```
python3 -m venv .venv
```

Use the following command to activate the virtual environment for a MAC os:

```
source .venv/bin/activate
```

If you’re on a Windows platform, activate the virtual environment as follows:

```
.venv\Scripts\activate.bat
```

```
python3 -m pip install --upgrade pip
```

Install the required dependencies:

```
pip install -r requirements.txt
```


update the values in the .env file



Before you deploy any AWS CDK application, you need to bootstrap a space in your account and the Region you’re deploying into. To bootstrap in your default Region, issue the following command:

```
cdk bootstrap
```

If you want to deploy into a specific account and Region, issue the following command:

```
cdk bootstrap aws://ACCOUNT-NUMBER/REGION
```
* `cdk synth`    - Emits the synthesized AWS CloudFormation template
 * `cdk deploy`    - Deploys this stack to your default AWS account and Region
 #### Go to the AWS Console
 - navigate to Amazon Connect using the search bar at the top left
 - select your instance alias
 - navigate to flows
 - click the dropdown to select the EmailAutomation-LambdaFunction lambda
 - attach the lambda
 - Once you have attached your lambda in the search box at the top of the page type Bedrock
 - Select Amazon Bedrock
 - Click the hamburger menu on the left hand side
 - Scroll to the bottom on the left hand side of the page to Bedrock configurations
 - Click Model access
 - Under Anthropic make sure that Claude Haiku shows the Access status of "Access granted"
    - If not click the orange button at the top of the page that says "Modify model access"
    - Click the box next to Claude 3 Haiku
    - Scroll to the bottom of the page and click next
    - Review and submit the access request "You should see a status of "Access granted"
    
 #### Go to your Amazon Connect Instance
 - go to Contact Flows
 - find the contact flow EmailRoutingIntelligence
 - go to the Lambda block
 - select the lambda function from the drop down
 - you should see 4 set queue blocks and will likely have to reselect the queue for each
 - once complete click Publish and the flow will save and publish for testing
 - assign the queues to the routing profile(s) of your choice and ensure that the email channel is checked
 - attach the flow to the email address of your choice and you are ready to test.
 
 #### Clean-up
 - In the Amazon Connect Instance:
   - Remove the Contact Flow association to email address(s)
   - Remove the Queue associations to routing profile(s)
 - Once the above has been done: 
   - In the CLI execute the command cdk destroy --all
