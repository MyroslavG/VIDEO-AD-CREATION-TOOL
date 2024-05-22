# ========================================================
# Developed by Vozniak Myroslav (Amuser), Date: 2024-05-22
# ProjectName: OutfitAI AD Generator
# ========================================================

# mkdir -p ~/miniconda3
# wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
# bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
# rm -rf ~/miniconda3/miniconda.sh
# cp ~/miniconda3/bin/conda /sbin/
# conda init
# exit

# mkdir outfitai
# chmod 777 outfitai
# cd outfitai
# conda create -n outfitai python==3.10
# conda activate outfitai
# apt-get install libgl1
# git clone https://github.com/TonyAssi/Segment-Body.git
# cd Segment-Body
# pip install -r requirements.txt
# cp ./SegBody.py ..
# cd ..
# pip install diffusers accelerate pillow rembg

from diffusers import AutoPipelineForInpainting, AutoencoderKL
from diffusers.utils import load_image
from SegBody import segment_torso
from PIL import Image
from rembg import remove
import torch
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

model_file = os.getenv('MODEL_FILE')
model_nobg_file = os.getenv('MODEL_NOBG_FILE')
outfit_file = os.getenv('OUTFIT_FILE')
outfit_nobg_file = os.getenv('OUTFIT_NOBG_FILE')
model_outfit_file = os.getenv('MODEL_OUTFIT_FILE')


def update_task(data):
    # Placeholder function for scalability.
    # Intended to update a record in the "task" database table and populate the following fields:
    # outfit_image_url, status_id
    return True

def retrieve_task():
    # Placeholder function for scalability.
    # Intended to get a record from the "task" database table :
    return True

# Function to remove background from an image
def remove_background(image_path, output_path):
    try:
        # Placeholder for background removal implementation
        input = Image.open(image_path)  
        output = remove(input) 
        output.save(output_path)
        logger.info(f"Background removed from {image_path}, saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error removing background from {image_path}: {e}")
        return False

# Function to add a white background to an image
def add_white_background(image_path, output_path):
    try:
        # Placeholder for adding white background implementation
        image = Image.open(image_path)
        new_image = Image.new("RGBA", image.size, (255, 255, 255, 255))
        new_image.paste(image, (0, 0), image)
        new_image = new_image.convert("RGB")
        new_image.save(output_path)
        logger.info(f"White background added to {image_path}, saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error adding white background to {image_path}: {e}")
        return False

# Function to perform virtual try-on
def virtual_try_on(img, clothing, prompt, negative_prompt, ip_scale=1.0, strength=0.99, guidance_scale=7.5, steps=100):
    try:
        _, mask_img = segment_torso(img) #, face=False)
        pipeline.set_ip_adapter_scale(ip_scale)

        clothing = clothing.resize((312, 512))
        mask_img = mask_img.resize((256, 512))

        images = pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=img,
            mask_image=mask_img,
            ip_adapter_image=clothing,
            strength=strength,
            guidance_scale=guidance_scale,
            num_inference_steps=steps,
        ).images
        logger.info("Virtual try-on completed successfully")
        return images[0]
    except Exception as e:
        logger.error(f"Error during virtual try-on: {e}")
        return None

# Load VAE and pipeline
try:
    vae = AutoencoderKL.from_pretrained("madebyollin/sdxl-vae-fp16-fix", torch_dtype=torch.float16)
    pipeline = AutoPipelineForInpainting.from_pretrained("diffusers/stable-diffusion-xl-1.0-inpainting-0.1", vae=vae, torch_dtype=torch.float16, variant="fp16", use_safetensors=True).to("cuda")
    pipeline.load_ip_adapter("h94/IP-Adapter", subfolder="sdxl_models", weight_name="ip-adapter_sdxl.bin", low_cpu_mem_usage=True)
    logger.info("Model and pipeline loaded successfully")
except Exception as e:
    logger.error(f"Error loading model and pipeline: {e}")

# Main process
try:
    data = retrieve_task()
    model_file = data['model_image_url']
    outfile_file = data['product_image_url']

    if remove_background(model_file, model_nobg_file) and add_white_background(model_nobg_file, model_nobg_file):
        if remove_background(outfit_file, outfit_nobg_file) and add_white_background(outfit_nobg_file, outfit_nobg_file):
            image = load_image(model_nobg_file).convert("RGB")
            ip_image = load_image(outfit_nobg_file).convert("RGB")

            img = virtual_try_on(img=image,
                                 clothing=ip_image,
                                 prompt="photorealistic, perfect body, beautiful skin, realistic skin, natural skin",
                                 negative_prompt="ugly, bad quality, bad anatomy, deformed body, deformed hands, deformed feet, deformed face, deformed clothing, deformed skin, bad skin, leggings, tights, stockings")
            if img:
                resized_img = img.resize((256, 512))
                resized_img.save('/tmp/' + model_outfit_file)
                logger.info("Output image saved as " + model_outfit_file)

            try:
                s3 = boto3.client('s3',
                            aws_access_key_id=aws_access_key_id,
                            aws_secret_access_key=aws_secret_access_key,
                            region_name=region_name)
                s3_bucket = os.getenv('S3_BUCKET_NAME')
                if not s3_bucket:
                    logger.error("S3_BUCKET_NAME environment variable not set")
                    exit()
                s3.upload_file('/tmp/' + model_outfit_file, s3_bucket, model_outfit_file)
                logger.info(f"Audio file uploaded to S3 bucket {s3_bucket}")
            except Exception as e:
                logger.error(f"Error uploading file to S3: {e}")
                exit()

            update_task([])
except Exception as e:
    logger.error(f"Error in main process: {e}")