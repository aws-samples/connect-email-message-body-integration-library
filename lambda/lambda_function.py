import json
import boto3
import os
import re
import datetime
import urllib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from urllib.request import urlopen

# Enable logging if environment variable is set to 'true'
enable_logging = os.environ.get('ENABLE_LOGGING', 'true') == 'true'

# Define the Bedrock model ID
model_id = "anthropic.claude-3-haiku-20240307-v1:0"
connectClient = boto3.client('connect')
s3Client = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime')

def lambda_handler(event, context):
    # Define trigger event
    myevent = event["Details"]["ContactData"]
    # Define required values: 
    instName = os.environ['instName']
    emailBucket = os.environ['connectBucket']
    
    # Extract email content from the Amazon Connect event
    email_content = extract_email_content(myevent)

    # Define the instruction for Bedrock
    instruction = """
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
    """
    
    # Call Bedrock to analyze the email content
    bedrock_result = call_bedrock(bedrock, model_id, instruction, email_content)
    
    if bedrock_result['success']:
        result_data = bedrock_result['data']
        
        # Prepare the response for Amazon Connect
        connect_response = {
            'intent1': result_data['intents'][0] if result_data['intents'] else '',
            'pii_detected': 'true' if result_data['pii_detected'] else 'false',
            'user_intent': result_data['user_intent'],
            # Flatten the extracted_info structure
            'phone_number': result_data['extracted_info'].get('phone_number', ''),
            'email_address': result_data['extracted_info'].get('email_address', ''),
            'name': result_data['extracted_info'].get('name', ''),
            'address': result_data['extracted_info'].get('address', ''),
            'account_number': result_data['extracted_info'].get('account_number', '')
        }
        
        # Add other_pii as a comma-separated string if it exists
        if result_data['extracted_info'].get('other_pii'):
            connect_response['other_pii'] = ','.join(result_data['extracted_info']['other_pii'])
        
        return connect_response
    else:
        # In case of an error, return an error response
        return {
            'error': 'An error occurred while processing the email'
        }
        
def extract_email_content(myevent):
    # Grab data from the event message
    subject = myevent["Name"]
    instId = myevent["InstanceARN"].split('/')[1]
    contactId = myevent["ContactId"]
    prevContactId = myevent["PreviousContactId"]
    contactArn = myevent["InstanceARN"]+"/contact/"+contactId
    myBodyReference = ''
    for myReference in myevent["References"]:
        if myevent["References"][myReference]["Type"] == "EMAIL_MESSAGE":
            myBodyReference = myReference
    
    # Look for main body and attachments
    response = connectClient.list_contact_references(
        InstanceId=instId,
        ContactId=contactId,
        ReferenceTypes=[
            'ATTACHMENT','EMAIL','EMAIL_MESSAGE'
        ]
    )

    myRefSumList = response['ReferenceSummaryList'][0]

    # Grab the email message file information. Should only be one.
    bodyFileId = myRefSumList['EmailMessage']['Name']
    bodyArn = myRefSumList['EmailMessage']['Arn']
    
    # get_attached_file uses the contactid ARN, not the returned ARN in the References.
    response = connectClient.get_attached_file(
        InstanceId=instId,
        FileId=bodyFileId,
        UrlExpiryInSeconds=60,
        AssociatedResourceArn=contactArn
    )
    
    bodyFileUrl = response["DownloadUrlMetadata"]["Url"]

    bodyContent = 'No Message Found'
    
    # Grab the message text for the body
    with urllib.request.urlopen(bodyFileUrl) as url:
        bodyFileJson = json.load(url)
        bodyContent = bodyFileJson["messageContent"]
    c = process_body(bodyContent)
    content = clean_string(c)
    print("the content for LLM is ", content)
    
    return content
    
def process_body(bodyContent):
    # Remove any HTML tags
    clean_content = re.sub(r'<[^>]+>', '', bodyContent)
    
    # Remove any leading/trailing whitespace
    clean_content = clean_content.strip()
    
    # Split the content into lines
    lines = clean_content.split('\n')
    
    # Find the start of the email body
    body_start = 0
    for i, line in enumerate(lines):
        if line.strip() == '':
            body_start = i + 1
            break
    
    # Extract the body
    c = '\n'.join(lines[body_start:])
    
    return c

def call_bedrock(bedrock, model_id, instruction, email_content):
    request_body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "system": instruction,
        "messages": [
            {
                "role": "user",
                "content": email_content
            }
        ],
        "temperature": 0
    })
    
    if enable_logging:
        print(f"Request body: {request_body}")
    
    try:
        response = bedrock.invoke_model(
            body=request_body,
            modelId=model_id,
            accept='application/json',
            contentType='application/json'
        )
        
        response_body = json.loads(response['body'].read())
        
        if enable_logging:
            print("Response body:", response_body)
        
        result = json.loads(clean_string(response_body["content"][0]["text"]))
        
        if enable_logging:
            print("Parsed result:", result)
        
        return {"success": True, "data": result}
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"success": False, "data": str(e)}

def clean_string(s):
    # Remove excess whitespace while preserving single spaces between words
    s = re.sub(r'\s+', ' ', s)
    # Trim leading and trailing spaces
    return s.strip()