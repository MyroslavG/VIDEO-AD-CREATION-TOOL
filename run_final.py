# ========================================================
# Developed by Vozniak Myroslav (Amuser), Date: 2024-05-22
# ProjectName: OutfitAI AD Generator
# ========================================================

# pip install moviepy boto3

import logging
from moviepy.editor import VideoFileClip, AudioFileClip
import os
import boto3
import tempfile

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Load environment variables from .env file
bucket_name = os.getenv('S3_BUCKET_NAME')
video_key = os.getenv('VIDEO_FILE')
audio_key = os.getenv('AUDIO_FILE')
output_key = os.getenv('FINAL_FILE')
aws_access_key_id = os.getenv('AWS_ACCESS_KEY')
aws_secret_access_key = os.getenv('AWS_SECRET_KEY')
region_name = os.getenv('AWS_REGION')

# Initialize the S3 client
s3 = boto3.client('s3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name)


def update_task(data):
    # Placeholder function for scalability.
    # Intended to update a record in the "task" database table and populate the following fields:
    # video_url, status_id
    return True

def retrieve_task():
    # Placeholder function for scalability.
    # Intended to get a record from the "task" database table
    return True


def download_file_from_s3(bucket_name, s3_key, local_path):
    # Download a file from S3 to a local path.
    try:
        logger.info(f"Downloading {s3_key} from bucket {bucket_name} to {local_path}")
        s3.download_file(bucket_name, s3_key, local_path)
        logger.info(f"Downloaded {s3_key} successfully")
    except Exception as e:
        logger.error(f"Failed to download {s3_key}: {e}")

def upload_file_to_s3(local_path, bucket_name, s3_key):
    # Upload a file from a local path to S3.
    try:
        logger.info(f"Uploading {local_path} to bucket {bucket_name} as {s3_key}")
        s3.upload_file(local_path, bucket_name, s3_key, ExtraArgs={'ACL': 'public-read'})
        logger.info(f"Uploaded {local_path} successfully")
    except Exception as e:
        logger.error(f"Failed to upload {local_path}: {e}")

def concatenate_video_audio(bucket_name, video_s3_key, audio_s3_key, output_s3_key):
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            logger.info(f"Created temporary directory: {temp_dir}")
            
            # Define local file paths
            local_video_path = f"{temp_dir}/video.mp4"
            local_audio_path = f"{temp_dir}/audio.mp3"
            local_output_path = f"{temp_dir}/output.mp4"
            
            # Download video file from S3
            download_file_from_s3(bucket_name, video_s3_key, local_video_path)
            
            # Download audio file from S3
            download_file_from_s3(bucket_name, audio_s3_key, local_audio_path)
            
            # Load the video file
            logger.info(f"Loading video file: {local_video_path}")
            video = VideoFileClip(local_video_path)
            
            # Load the audio file
            logger.info(f"Loading audio file: {local_audio_path}")
            audio = AudioFileClip(local_audio_path)
            
            # Set the audio of the video to the loaded audio file
            logger.info("Setting audio for the video")
            final_video = video.set_audio(audio)
            
            # Write the final video file locally
            logger.info(f"Writing the output video file to: {local_output_path}")
            final_video.write_videofile(local_output_path, codec='libx264', audio_codec='aac')
            
            logger.info("Video and audio concatenation completed successfully")
            
            # Upload the final video file to S3
            upload_file_to_s3(local_output_path, bucket_name, output_s3_key)
        
        except Exception as e:
            logger.error(f"An error occurred: {e}")

# Main process
try:
  data = retrieve_task()
  concatenate_video_audio(
    bucket_name=bucket_name,
    video_s3_key=video_key,
    audio_s3_key=audio_key,
    output_s3_key=output_key
  )
  update_task([])
except Exception as e:
    logger.error(f"An error occurred: {e}")  