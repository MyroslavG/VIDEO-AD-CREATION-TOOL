# ========================================================
# Developed by Vozniak Myroslav (Amuser), Date: 2024-05-22
# ProjectName: OutfitAI AD Generator
# ========================================================

# git clone https://github.com/AliaksandrSiarohin/first-order-model
# cd first-order-model
# pip install -r requirements.txt
# mkdir checkpoints
# cd checkpoints
# download into checkpoints eg fasion.pth.tar from https://drive.google.com/drive/folders/1PyQJmkdCsAkOYwUyaj_l-l0as-iLDgeH
# download template for moving eg fashion.mov

# python demo.py --config config/fashion-256.yaml 
#   --driving_video fashion.mov 
#   --source_image output3.png 
#   --checkpoint checkpoints/fashion.pth.tar 
# --relative --adapt_scale --result_video /tmp/result.mp4

import subprocess
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
aws_access_key_id = os.getenv('AWS_ACCESS_KEY')
aws_secret_access_key = os.getenv('AWS_SECRET_KEY')
region_name = os.getenv('AWS_REGION')

def update_task(data):
    # Placeholder function for scalability.
    # Intended to update a record in the "task" database table and populate the following fields:
    # outfit_image_url, status_id
    return True

def retrieve_task():
    # Placeholder function for scalability.
    # Intended to get a record from the "task" database table
    return True


data = retrieve_task()
model_outfit_file = data['model_outfit_file']
video_file = os.getenv('VIDEO_FILE')
s3_bucket = os.getenv('S3_BUCKET_NAME')

# Define the command and its arguments
command = [
    "python", "demo.py",
    "--config", "config/fashion-256.yaml",
    "--driving_video", "fashion.mov",
    "--source_image", model_outfit_file,
    "--checkpoint", "checkpoints/fashion.pth.tar",
    "--relative",
    "--adapt_scale",
    "--result_video", "/tmp/" + video_file
]

# Run the command
try:
    result = subprocess.run(command, check=True, capture_output=True, text=True)

    try:
        s3 = boto3.client('s3',
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    region_name=region_name)
        s3_bucket = os.getenv('S3_BUCKET_NAME')
        if not s3_bucket:
            logger.error("S3_BUCKET_NAME environment variable not set")
            exit()
        s3.upload_file('/tmp/' + video_file, s3_bucket, video_file)
        logger.info(f"Audio file uploaded to S3 bucket {s3_bucket}")
    except Exception as e:
        logger.error(f"Error uploading file to S3: {e}")
        exit()

    update_task([])

except subprocess.CalledProcessError as e:
    print(f"Command '{e.cmd}' returned non-zero exit status {e.returncode}")
    print(e.output)
except Exception as e:
    print(f"An error occurred: {e}")

