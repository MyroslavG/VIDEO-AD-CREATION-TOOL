# ========================================================
# Developed by Vozniak Myroslav (Amuser), Date: 2024-05-22
# ProjectName: OutfitAI AD Generator
# ========================================================

# Deployment Steps:

# Package Dependencies:
#     Use pip to install dependencies (requests, boto3, bs4) into a local directory:
#     pip install requests boto3 bs4 -t .
#     Zip your Lambda function code along with the installed dependencies:
#     zip -r9 function.zip .

# Create Lambda Function:
#     Use AWS Management Console or AWS CLI to create the Lambda function, specifying the ZIP file created above as the deployment package.

# Set Environment Variables:
#     Configure necessary environment variables (e.g., AMAZON_URL, S3_BUCKET_NAME) in the Lambda function configuration.

# Permissions:
#     Ensure the Lambda execution role has permissions to access Amazon Polly, S3, and any other necessary AWS resources.

import requests
from bs4 import BeautifulSoup
import boto3
import os
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

aws_access_key_id = os.getenv('AWS_ACCESS_KEY')
aws_secret_access_key = os.getenv('AWS_SECRET_KEY')
region_name = os.getenv('AWS_REGION')


def create_task(data):
    # Placeholder function for scalability.
    # Intended to create a record in the "task" database table and populate the following fields:
    # task_id, product_url, product_desc, product_image, s3_audio_url, model_url, outfit_image_url, video_url, status_id
    return True

def scrape_amazon_product(url):
    # Scrape the Amazon product page for title and description
    logger.info(f"Scraping Amazon product page: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    response = requests.get(url, headers=headers, cookies={'__hs_opt_out': 'no'})
    soup = BeautifulSoup(response.content, 'html.parser')
    title = soup.find('span', {'id': 'productTitle'}).text.strip()
    description = soup.find('div', {'id': 'productDescription'}).text.strip()
    logger.info(f"Product title: {title}")
    return title, description

def text_to_speech(text, output_file):
    # Convert text to speech using Amazon Polly and save to a file
    logger.info("Converting text to speech")
    polly = boto3.client('polly', 
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    region_name=region_name)
    
    response = polly.synthesize_speech(
        Text=text,
        OutputFormat='mp3',
        VoiceId=os.getenv('VoiceId', 'Joanna')  # Default to 'Joanna' if VoiceId is not set
    )
    
    with open(output_file, 'wb') as file:
        file.write(response['AudioStream'].read())
    logger.info(f"Audio file saved to {output_file}")

def lambda_handler(event, context):
    # Main Lambda function handler
    logger.info("Lambda function started")

    # Get the Amazon URL from environment variables
    url = os.getenv('AMAZON_URL')
    if not url:
        logger.error("AMAZON_URL environment variable not set")
        return {
            'statusCode': 400,
            'body': 'AMAZON_URL environment variable not set'
        }
    
    audio_file = os.getenv('AUDIO_FILE')
    output_file = '/tmp/' + audio_file  # Lambda allows write access to /tmp
    
    try:
        title, description = scrape_amazon_product(url)
    except Exception as e:
        logger.error(f"Error scraping Amazon product: {e}")
        return {
            'statusCode': 500,
            'body': f"Error scraping Amazon product: {e}"
        }
    
    try:
        text_to_speech(description, output_file)
    except Exception as e:
        logger.error(f"Error converting text to speech: {e}")
        return {
            'statusCode': 500,
            'body': f"Error converting text to speech: {e}"
        }
    
    try:
        s3 = boto3.client('s3',
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    region_name=region_name)
        s3_bucket = os.getenv('S3_BUCKET_NAME')
        if not s3_bucket:
            logger.error("S3_BUCKET_NAME environment variable not set")
            return {
                'statusCode': 400,
                'body': 'S3_BUCKET_NAME environment variable not set'
            }
        s3.upload_file(output_file, s3_bucket, audio_file)
        logger.info(f"Audio file uploaded to S3 bucket {s3_bucket}")
    except Exception as e:
        logger.error(f"Error uploading file to S3: {e}")
        return {
            'statusCode': 500,
            'body': f"Error uploading file to S3: {e}"
        }
    
    create_task([])
    return {
        'statusCode': 200,
        'body': {
            'title': title,
            'description': description,
            's3_audio_url': f"s3://{s3_bucket}/" + audio_file
        }
    }