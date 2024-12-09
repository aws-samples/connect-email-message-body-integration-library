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
    language_code = detect_language(email_content)
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
            'account_number': result_data['extracted_info'].get('account_number', ''),
            'language': language_code
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
    try:
        # Log the incoming event for debugging
        if enable_logging:
            print(f"Incoming event: {json.dumps(myevent, indent=2)}")

        # Grab data from the event message
        instId = myevent["InstanceARN"].split('/')[1]
        contactId = myevent["ContactId"]
        contactArn = myevent["InstanceARN"]+"/contact/"+contactId

        # First, try to get the email reference directly from the event
        if "References" in myevent:
            if enable_logging:
                print(f"References found in event: {json.dumps(myevent['References'], indent=2)}")
            
            # Look for email reference in the event
            for ref_key, ref_value in myevent["References"].items():
                if enable_logging:
                    print(f"Checking reference: {ref_key} = {json.dumps(ref_value, indent=2)}")
                
                if isinstance(ref_value, dict) and ref_value.get("Type") == "EMAIL_MESSAGE":
                    if enable_logging:
                        print(f"Found EMAIL_MESSAGE reference: {json.dumps(ref_value, indent=2)}")
                    
                    # Try different possible value fields
                    file_id = (ref_value.get("Value") or 
                             ref_value.get("Reference") or 
                             ref_value.get("Id") or 
                             ref_key)  # Use the reference key itself as a last resort
                    
                    if file_id:
                        if enable_logging:
                            print(f"Using file_id: {file_id}")
                        break
            else:
                if enable_logging:
                    print("No valid EMAIL_MESSAGE reference found in References")
                file_id = None
        else:
            if enable_logging:
                print("No References found in event")
            file_id = None

        # If we didn't find a file_id in References, try list_contact_references
        if not file_id:
            if enable_logging:
                print("Attempting to get references using list_contact_references")

            response = connectClient.list_contact_references(
                InstanceId=instId,
                ContactId=contactId,
                ReferenceTypes=['EMAIL_MESSAGE']
            )

            if enable_logging:
                print(f"list_contact_references response: {json.dumps(response, indent=2)}")

            if response.get('ReferenceSummaryList'):
                email_ref = response['ReferenceSummaryList'][0]
                if enable_logging:
                    print(f"Found reference summary: {json.dumps(email_ref, indent=2)}")
                
                # Try all possible fields for the file ID
                file_id = (email_ref.get('Value') or 
                          email_ref.get('Reference') or 
                          email_ref.get('Name') or 
                          email_ref.get('Id'))

        if not file_id:
            # Try to get the message directly from the event
            if 'Attributes' in myevent and 'body' in myevent['Attributes']:
                return clean_string(process_body(myevent['Attributes']['body']))
            
            if enable_logging:
                print("Available event data:")
                print(f"Event keys: {list(myevent.keys())}")
                if 'References' in myevent:
                    print(f"References keys: {list(myevent['References'].keys())}")
                if 'Attributes' in myevent:
                    print(f"Attributes keys: {list(myevent['Attributes'].keys())}")
            
            raise ValueError("Could not find file ID in email reference")

        # Get the attached file using the correct parameters
        if enable_logging:
            print(f"Getting attached file with ID: {file_id}")

        file_response = connectClient.get_attached_file(
            InstanceId=instId,
            FileId=file_id,
            AssociatedResourceArn=contactArn
        )

        if enable_logging:
            print(f"get_attached_file response: {json.dumps(file_response, indent=2)}")

        if ('DownloadUrlMetadata' not in file_response or 
            'Url' not in file_response['DownloadUrlMetadata']):
            raise ValueError("Failed to get download URL for email content")

        download_url = file_response['DownloadUrlMetadata']['Url']

        # Fetch and process the email content
        with urllib.request.urlopen(download_url) as url:
            email_json = json.load(url)
            
            if enable_logging:
                print(f"Email JSON content keys: {list(email_json.keys())}")

            # Try multiple possible field names for the content
            content = (email_json.get('messageContent') or 
                      email_json.get('content') or 
                      email_json.get('body') or 
                      email_json.get('text') or 
                      email_json.get('message'))
            
            if not content:
                if enable_logging:
                    print(f"Available fields in email_json: {list(email_json.keys())}")
                raise ValueError("No message content found in email file")

            return clean_string(process_body(content))

    except Exception as e:
        if enable_logging:
            print(f"Error in extract_email_content: {str(e)}")
            print(f"Full event data: {json.dumps(myevent, indent=2)}")
        raise

def process_body(bodyContent):
    try:
        if not bodyContent:
            return ""
        
        if not isinstance(bodyContent, str):
            bodyContent = str(bodyContent)

        # Remove any HTML tags
        clean_content = re.sub(r'<[^>]+>', '', bodyContent)
        # Remove any leading/trailing whitespace
        clean_content = clean_content.strip()
        
        return clean_content

    except Exception as e:
        if enable_logging:
            print(f"Error in process_body: {str(e)}")
        return bodyContent

def detect_language(email_content):
    # Detect the language of the text
    comprehend = boto3.client('comprehend')
    response = comprehend.detect_dominant_language(Text=email_content)
    language_code = response['Languages'][0]['LanguageCode']
    return language_code

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