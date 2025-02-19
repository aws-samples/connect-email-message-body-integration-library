# Prerequisites

You must have the following prerequisites to use this sample code:

* [AWS account](https://signin.aws.amazon.com/signin)
* [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
    * If you don’t already have the AWS CLI on your local machine in your dev tool of choice, refer to [Installing or updating the latest version of the AWS CLI and Configuring the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).
    * Make sure you have [AWS CLI credentials](https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-files.html) configured for your dev tool
* [AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/prerequisites.html) latest version
* [Python 3.11](https://www.python.org/downloads/) or later
* An [Amazon Connect](https://docs.aws.amazon.com/connect/latest/adminguide/what-is-amazon-connect.html) instance with [Amazon Connect Email](https://docs.aws.amazon.com/connect/latest/adminguide/what-is-amazon-connect.html) enabled

## Initial setup

Using your dev tool of choice:

* Clone the [connect-email-message-body-integration-library](https://github.com/aws-samples/connect-email-message-body-integration-library.git) to your preferred dev tool like VS Code
* Open the terminal of your dev tool
* Install the AWS CDK Toolkit globally using the following node package manager command:
```
npm install -g aws-cdk-lib@latest
```
### Enter your account details in the .env file

Using your dev tool of choice:

* Open the .env file that came with the cloned GitHub repository
* Edit the follow with your account details:

CONNECT_BUCKET=your-connect-s3-bucket
INSTANCE_NAME=your-connect-instance-name
CONNECT_INSTANCE_ARN=your-connect-instance-arn
HOURS_OF_OPERATION_ARN=your-connect-instance-hours-of-opperation-arn

* Example of  .env file after entering account details:

CONNECT_BUCKET=amazon-connect-aaabbbccc112233
INSTANCE_NAME=myconnectinstance
CONNECT_INSTANCE_ARN=arn:aws:connect:us-west-2:01234567890:instance/aaabbbccc-1234-abcd-5678-aaabbbcccdddd
HOURS_OF_OPERATION_ARN=aws:connect:us-west-2:01234567890:instance/aaabbbccc-1234-abcd-5678-aaabbbcccdddd/operating-hours/aaabbbccc-1234-abcd-5678-aaabbbcccdddd

* If you need help getting details:
    * [Amazon S3 bucket name](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html#bucket-names)
    * [Amazon Connect instance ID or ARN](https://docs.aws.amazon.com/connect/latest/adminguide/find-instance-arn.html)
    * [Amazon Connect Hours of Operation](https://docs.aws.amazon.com/connect/latest/adminguide/set-hours-operation.html)

#### Setup a virtual environment

This project is set up like a standard Python project. 

* Create a Python virtual environment using the following code:

```
python3 -m venv .venv
```

**MacOS/Linux activation command:**
* Use the following command to activate the virtual environment for a MacOS/Linux:

```
source .venv/bin/activate
```

**Windows activation command**
* Use the following command to activate the virtual environment for a Windows:

```
.venv\Scripts\activate.bat
```
**Update to the latest version of pip and install requirements**
* Update pip command:

```
python3 -m pip install --upgrade pip
```

* Install the required dependencies into the Python project:

```
pip install -r requirements.txt
```
##### Bootstrap, synthesize, and deploy the AWS CDK project
Before you deploy any AWS CDK application built with this sample code, you need to bootstrap a space in your AWS account and the AWS region you’re deploying into. 

* To bootstrap in your default AWS region, issue the following command:

```
cdk bootstrap
```

* To bootstrap to a specific AWS account and region, issue the following command:

```
cdk bootstrap aws://ACCOUNT-NUMBER/REGION
```
* If you need help getting details:
    * [Viewing your AWS account ID](https://docs.aws.amazon.com/IAM/latest/UserGuide/console-account-id.html)
    * [AWS Regions and Availability Zones](https://aws.amazon.com/about-aws/global-infrastructure/regions_az/)

* Synthesize the AWS CDK project which emits the synthesized AWS CloudFormation template into your AWS account:
```
cdk synth
```
* Deploy the AWS CDK project which deploys this stack to your default AWS account and region
```
cdk deploy
```
* You will need to respond with y when asked Do you wish to deploy these changes (y/n)?

You’re done with your development, packaging, and deployment of the sample code from the AWS CDK project in your dev tool of choice. The rest of the configuration is done via the [AWS Console](https://docs.aws.amazon.com/signin/latest/userguide/how-to-sign-in.html) and your [Amazon Connect instance](https://docs.aws.amazon.com/connect/latest/adminguide/find-instance-name.html).

###### Add Lambda generated from AWS CDK project to Connect instance

* Navigate to the AWS Console 
* Navigate to Amazon Connect using the [AWS Console search bar](https://docs.aws.amazon.com/resource-explorer/latest/userguide/using-unified-search.html)
* Select your [Amazon Connect instance alias](https://docs.aws.amazon.com/connect/latest/adminguide/find-instance-name.html)
* Navigate to Flows on the left side navigation in the Amazon Connect Console
* Scroll down to AWS Lambda
* Click the “Lambda Functions” dropdown to select the AWS Lambda named something like: EmailAutomation-LambdaFunction-aaabbbccc111-dddeefff222
* Click “+ Add Lambda Function” to attach the AWS Lambda to your Amazon Connect instance

###### Configure Amazon Bedrock models available in your AWS account

* Once you have attached your AWS Lambda to your Amazon Connect instance
* Navigate to Amazon Bedrock using the [AWS Console search bar](https://docs.aws.amazon.com/resource-explorer/latest/userguide/using-unified-search.html)
* In Amazon Bedrock, click the hamburger menu (three stacked lines) on the left side navigation in the Amazon Bedrock Console
* Scroll to the bottom of the left side navigation in the Amazon Bedrock Console to “Bedrock configurations”
* Click “Model access” under “Bedrock configurations” 
* Under the Anthropic section, make sure that the “Claude Haiku” row shows the “Access status” of “✅ Access granted”
    * If it does not show “✅ Access granted”, click the orange button at the top of the page that says "Modify model access" to toggle the table to allow selections of models
    * Check the box in the “Claude 3 Haiku” row
    * Scroll to the bottom of the page and click “Next”
    * This will take you to the “Review and submit” page where you should see a status of "Access granted"
    * Click “Submit” to enable the Amazon Bedrock model for your account

###### Configure Amazon Connect resources generated from AWS CDK project

* Once you have enabled the Amazon Bedrock models required
* Navigate to Amazon Connect using the [AWS Console search bar](https://docs.aws.amazon.com/resource-explorer/latest/userguide/using-unified-search.html)
* Open your [Amazon Connect instance](https://docs.aws.amazon.com/connect/latest/adminguide/find-instance-name.html) to get to the admin UI
* Navigate to Routing>Flows
* Search for the contact flow “EmailRoutingIntelligence” that was generated in your Connect instance and open it
* Locate the Lambda block in the flow and click on it to open the block’s properties
* Under “Function ARN” under “Set manually” select the EmailAutomation-LambdaFunction-aaabbbccc111-dddeefff222 AWS Lambda from step 6 from the dropdown
* Click “Save” to save your changes
* Locate the 4 “Set working queue blocks” in the flow that assign the email contacts to the following queues: “HomeEquity”, “CarLoan”, “HomeLoan”, and “Unknown” - these might cause an error that requires you to reselect the queues from the dropdown list of the block’s properties
* To keep the flow the same, click “Publish” to save and publish the flow as is for testing
* Navigate to Users>Routing Profiles to assign the “HomeEquity”, “CarLoan”, “HomeLoan”, and “Unknown” queues to the agent routing profile(s) of your choice to test
* Ensure that you have “Email” checked under the “Channels” column
* Associate the “EmailRoutingIntelligence” flow to the email address of your choice to test

###### Built-in use cases to test

* Send in emails from your email client (e.g., Outlook) to the email address associated with the “EmailRoutingIntelligence” flow
* The Lambda will send your email message to Amazon Bedrock to be analyzed for the following use cases

**Routing based on intent use cases**

* Use language in your email like “I’m looking to apply for a home equity line of credit” to have the inbound email contact routed to agents assigned to the “HomeEquity” queue
* Use language in your email like “I would like to purchase a brand new car” to have the inbound email contact routed to agents assigned to the “CarLoan” queue
* Use language in your email like “I really want to purchase my dream home as my first home” to have the inbound email contact routed to agents assigned to the “HomeLoan” queue
* In the case Amazon Bedrock isn’t able to determine if the inbound email contact has a “HomeEquity”, “CarLoan”, or “HomeLoan” intents, the inbound email contact will be routed to agents assigned to the “Unknown” queue

**Customer entity and PII detection and attribute use cases**

* The Amazon Bedrock model will detect customer entities like account numbers, PII detected, intent, primary language used, phone numbers, and email addresses to be mapped to [user-defined attributes](https://docs.aws.amazon.com/connect/latest/adminguide/connect-attrib-list.html#user-defined-attributes) on the email contact that can be used in the flow
* Navigate to Analytics and optimization>Contact Lens>Contact search to see example outputs
* Open an email contact that was routed using the “EmailRoutingIntelligence” flow and assigned to one of the “HomeEquity”, “CarLoan”, “HomeLoan”, or “Unknown” queues 
* Scroll to “Attributes” to see the following customer entities that can be pulled from the email body from the customer’s message itself or their email signature:
    * account_number            23456789
    * detected_pii                    Caution PII has been detected in email
    * intent                                Request for help with home equity loan
    * language                           en
    * phone_number               +12345678910
    * pii                                       true
* If you would like to use these [user-defined attributes](https://docs.aws.amazon.com/connect/latest/adminguide/connect-attrib-list.html#user-defined-attributes) on the email contact to make routing decisions, escalate priority of email contacts, or assign to a specific supervisor queue (i.e., properly handling PII reviews), use the [Check contact attributes](https://docs.aws.amazon.com/connect/latest/adminguide/check-contact-attributes.html) flow block to branch based on the attribute values (e.g., language == en)

**Automating responses use cases**

* Depending on the results from Amazon Bedrock’s analysis of the email message from the email contact, you can use the [Send message](https://docs.aws.amazon.com/connect/latest/adminguide/send-message.html) flow block to automatically respond to a known issue (e.g., “I need help resetting my password”) using an [email template](https://docs.aws.amazon.com/connect/latest/adminguide/create-message-templates1.html) with [contact attributes](https://docs.aws.amazon.com/connect/latest/adminguide/connect-attrib-list.html) to [personalize the automted response](https://docs.aws.amazon.com/connect/latest/adminguide/personalize-templates.html) to the inbound email contact

###### Customize the generated Lambda for other use cases

You can customize the AWS Lambda provided with the AWS CDK project sample code to better fit your use cases and required outputs from Amazon Bedrock:

* Navigate to the AWS Console
* Navigate to Lambda using the [AWS Console search bar](https://docs.aws.amazon.com/resource-explorer/latest/userguide/using-unified-search.html)
* Select the ```EmailAutomation-LambdaFunction-aaabbbccc111-dddeefff222``` Lambda from the list of Lambdas in your AWS account
* Scroll down and open “Code” in the Lambda Console
* See the following details about adding custom intents, PII detection, and customer entities in the sample Python code:
```
Analyze the following email message and provide the following information in a JSON format:
    1. Intents: Detect all intentions of why the person is reaching out.
    2. PII: Detect if any Personally Identifiable Information is present, and if so, extract:
       - Phone number
       - Email address
       - Name
       - Address
       - Account number
       - Any other PII found
    3. User intent: Determine the primary reason for contact to assist with routing.
    Output format:
    {
        "intents": ["intent1", "intent2", ...],
        "pii_detected": true|false,
        "extracted_info": {
            "phone_number": "...",
            "email_address": "...",
            "name": "...",
            "address": "...",
            "account_number": "...",
            "other_pii": [...]
        },
        "user_intent": "primary_intent_for_routing"
    }
    Provide only the JSON output, no additional text or explanations.
```
* The sample Python code uses Amazon Connect [files APIs](https://docs.aws.amazon.com/connect/latest/APIReference/files-api.html) such as [GetAttachedFile](https://docs.aws.amazon.com/connect/latest/APIReference/API_GetAttachedFile.html) to access the email message from the email contact and send it to Amazon Bedrock to be analyzed
* You can customize the Amazon Bedrock model used to analyze the email message from the email contact
* While this sample code uses Python, it’s also possible to achieve the same integration using Lambda with other languages as well

# Appendix

## Common errors

**Error 1**
```
python3 : The term 'python3' is not recognized as the name of a cmdlet, function, script file, or operable program. Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:1 char:1
+ python3 -m venv .venv
+ ~~~~~~~
    + CategoryInfo          : ObjectNotFound: (python3:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
```
* Try using python instead of python3 

**Error 2**
```
ERROR: Could not install packages due to an OSError: [WinError 5] Access is denied: 'c:\\python312\\lib\\site-packages\\pip-24.0.dist-info\\AUTHORS.txt'
Consider using the `--user` option or check the permissions.
```
* Run ```python.exe -m pip install —upgrade pip```  to make sure pip is updated
* This error can be ignored if it cannot be resolved

**Error 3**
```
ERROR: Could not install packages due to an OSError: [WinError 2] The system cannot find the file specified: 'C:\\Python312\\Scripts\\dotenv.exe' -> 'C:\\Python312\\Scripts\\dotenv.exe.deleteme'
```
* This error can be ignored

**Error 4**
```
'python3' is not recognized as an internal or external command,
operable program or batch file.
Subprocess exited with error 1
Traceback (most recent call last):
  File "C:\connect-email-message-body-integration-library\app.py", line 1, in <module>
    from aws_cdk import (
ModuleNotFoundError: No module named 'aws_cdk'
Subprocess exited with error 1
```
* Use ```python``` instead of ```python3``` 
* Install a specific version of AWS CDK using ```pip install aws-cdk-lib==2.145.0```

**Error 5**
```
 ❌  Environment aws://01234567890/ca-central-1 failed bootstrapping: _AuthenticationError: Need to perform AWS calls for account 01234567890, but no credentials have been configured
    at async _BootstrapStack.lookup (C:\Users\USERNAME\AppData\Roaming\npm\node_modules\aws-cdk\lib\index.js:705:24948)
    at async Bootstrapper.modernBootstrap (C:\Users\USERNAME\AppData\Roaming\npm\node_modules\aws-cdk\lib\index.js:706:1115)
    at async C:\Users\USERNAME\AppData\Roaming\npm\node_modules\aws-cdk\lib\index.js:752:1556 {
  type: 'authentication'
}
Need to perform AWS calls for account 0123456790, but no credentials have been configured
```
* You need to configure your [AWS CLI credentials](https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-files.html) in the dev tool of your choice

#### Clean-up
 - In the Amazon Connect Instance:
   - Remove the Contact Flow association to email address(s)
   - Remove the Queue associations to routing profile(s)
 - Once the above has been done: 
   - In the CLI execute the command cdk destroy --all