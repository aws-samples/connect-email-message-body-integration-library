from aws_cdk import (
    App,
    Stack,
    aws_lambda as lambda_,
    aws_connect as connect,
    aws_iam as iam,
    CfnOutput,
    Duration,
)
from constructs import Construct
import os
from dotenv import load_dotenv
import json
import uuid
import logging
import subprocess
import shutil
import tempfile

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailAutomation(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Validate environment variables
        required_env_vars = ['CONNECT_INSTANCE_ARN', 'HOURS_OF_OPERATION_ARN', 'CONNECT_BUCKET', 'INSTANCE_NAME']
        for var in required_env_vars:
            if not os.environ.get(var):
                raise ValueError(f"Environment variable {var} is not set")

        connect_instance_arn = os.environ['CONNECT_INSTANCE_ARN']
        hours_of_operation_arn = os.environ['HOURS_OF_OPERATION_ARN']
        environment = {
           "connectBucket": os.environ['CONNECT_BUCKET'],
           "instName": os.environ['INSTANCE_NAME']
        }

        # Generate a unique ID for the contact flow
        contact_flow_id = str(uuid.uuid4())

        # Build the Lambda layer
        layer_asset_path = self.build_layer()

        # Create a Lambda Layer
        lambda_layer = lambda_.LayerVersion(
            self, "LambdaLayer",
            code=lambda_.Code.from_asset(layer_asset_path),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
            description="Lambda Layer for boto3 and other dependencies"
        )

        # Create a Python Lambda function
        lambda_fn = lambda_.Function(
            self, "LambdaFunction",
            code=lambda_.Code.from_asset("./lambda"),
            handler="lambda_function.lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_11,
            layers=[lambda_layer],
            environment=environment,
            timeout=Duration.seconds(30),
            memory_size=256,
            tracing=lambda_.Tracing.ACTIVE  # Enable X-Ray tracing
        )

        # Add IAM permissions for Amazon Connect API access (scoped down)
        lambda_fn.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "connect:*"
            ],
            resources=[f"{connect_instance_arn}/*"]
        ))

        # Add IAM permissions for Amazon Bedrock model access (Claude Haiku)
        lambda_fn.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "bedrock:InvokeModel"
            ],
            resources=[
                f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
            ]
        ))
        # Add IAM permissions for Amazon Comprehend DetectDominantLanguage
        lambda_fn.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "comprehend:DetectDominantLanguage"
            ],
            resources=["*"]
        ))

        # Create Queues
        queue_names = ["HomeEquity", "CarLoan", "HomeLoan", "Unknown"]
        queues = {}
        for queue_name in queue_names:
            queue = connect.CfnQueue(
                self, f"Queue{queue_name}",
                instance_arn=connect_instance_arn,
                name=queue_name,
                description=f"{queue_name} Specialists",
                hours_of_operation_arn=hours_of_operation_arn,
                tags=[{
                    "key": "Environment",
                    "value": "Production"
                    }, {
                    "key": "SecurityClassification",
                    "value": "Confidential"
                }]
            )
            queues[queue_name] = queue

        # Create Contact Flow
        try:
            with open("./email_assessor/Intent_Routing_Email_Flow.content.json", "r") as file:
                content = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error reading contact flow file: {str(e)}")
            raise

        # Update queue references in the content
        for action in content['Actions']:
            if action['Type'] == 'UpdateContactTargetQueue':
                queue_name = action['Parameters']['QueueId'].split('/')[-1]
                if queue_name in queues:
                    action['Parameters']['QueueId'] = queues[queue_name].attr_queue_arn

        cfn_contact_flow = connect.CfnContactFlow(self, "EmailRoutingContactFlow",
            content=json.dumps(content),
            instance_arn=connect_instance_arn,
            name="EmailRoutingIntelligence",
            type="CONTACT_FLOW",
            description="Inbound contact flow for email routing",
            state="ACTIVE",
        )

        # Outputs
        CfnOutput(self, "LambdaFunctionARN", value=lambda_fn.function_arn)
        CfnOutput(self, "LambdaLayerARN", value=lambda_layer.layer_version_arn)
        CfnOutput(self, "ContactFlowARN", value=cfn_contact_flow.attr_contact_flow_arn)
        for queue_name, queue in queues.items():
            CfnOutput(self, f"Queue{queue_name}ARN", value=queue.attr_queue_arn)

    def build_layer(self):
        """
        Build Lambda layer with specific boto3 version and dependencies
        Returns:
            str: Path to the created layer zip file
        """
        # Create a temporary directory
        layer_build_dir = tempfile.mkdtemp(prefix="lambda_layer_")
        
        try:
            # Create a directory for the layer
            layer_dir = os.path.join(layer_build_dir, 'python')
            os.makedirs(layer_dir)
            
            # Create requirements.txt with specific versions
            requirements_path = os.path.join(layer_build_dir, 'requirements.txt')
            with open(requirements_path, 'w') as f:
                f.write('boto3==1.34.34\n')
                f.write('botocore==1.34.34\n')
            
            # Install dependencies
            logger.info("Installing dependencies for Lambda layer...")
            subprocess.run([
                'pip3',
                'install',
                '-r', requirements_path,
                '-t', layer_dir,
                '--platform', 'manylinux2014_x86_64',
                '--only-binary=:all:'
            ], check=True)
            
            # Create a zip file of the layer contents
            logger.info("Creating Lambda layer zip file...")
            layer_zip = os.path.join(layer_build_dir, 'layer.zip')
            shutil.make_archive(os.path.join(layer_build_dir, 'layer'), 'zip', layer_dir)
            
            logger.info(f"Successfully created Lambda layer at: {layer_zip}")
            return layer_zip
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error building Lambda layer: {str(e)}")
            raise

app = App()
EmailAutomation(app, "EmailAutomation")
app.synth()