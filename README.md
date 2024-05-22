# OutfitAI AD Generator

## Developed by Vozniak Myroslav (Amuser)
**Date:** 2024-05-22

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture & Requirements](#requirements)
3. [Setup Instructions](#setup-instructions)
    - [run_scrape_audio.py](#run_scrape_audiopy)
    - [run_outfit.py](#run_outfitpy)
    - [run_animate.py](#run_animatepy)
    - [run_final.py](#run_finalpy)
4. [Environment Variables](#environment-variables)
5. [Future Improvements](#future-improvements)

## Project Overview
OutfitAI AD Generator is a project designed to automate the creation of advertising videos. The project involves scraping product data from Amazon, generating audio, applying outfits to a specified model, and animating the model with background narration.

## Architecture & Requirements
<img src="https://github.com/narkov/justai/blob/main/images/outfitai.png" width=500 /> 

- Python 3.x
- AWS Account with access to Polly, S3, and Lambda services
- GPU (recommended for `run_outfit.py` and `run_animate.py`)

## Setup Instructions

### run_scrape_audio.py
This script utilizes BeautifulSoup to scrape product data from Amazon pages. It then uses AWS Polly to generate MP3 speech from the scraped data, which is subsequently uploaded to an AWS S3 bucket.

#### Deployment Steps:

1. **Package Dependencies:**
    ```sh
    pip install requests boto3 bs4 -t .
    zip -r9 function.zip .
    ```

2. **Create Lambda Function:**
    - Use AWS Management Console or AWS CLI to create the Lambda function, specifying the ZIP file created above as the deployment package.

3. **Set Environment Variables:**
    - Configure necessary environment variables (e.g., `AMAZON_URL`, `S3_BUCKET_NAME`) in the Lambda function configuration.

4. **Permissions:**
    - Ensure the Lambda execution role has permissions to access Amazon Polly, S3, and any other necessary AWS resources.

### run_outfit.py
This script replaces the outfit for a model with one retrieved from an Amazon page. It processes both the model and the outfit images, initially removing their backgrounds. Then, it utilizes Stability Diffuse with inpaint functionality and h94/IP-Adapter to perform the outfit image replacement. We were testing the script on cheap tensordock.com servers. Here is the video of image generating.

#### Setup Steps:
1. Ensure you have a compatible GPU setup.
2. Install necessary libraries and dependencies (instructions will vary based on your specific setup and environment).
We use miniconda for virtual environment setup
```
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm -rf ~/miniconda3/miniconda.sh
cp ~/miniconda3/bin/conda /sbin/
conda init
exit
```

We also utilize the [Segment-Body](https://github.com/TonyAssi/Segment-Body.git) library to enhance body detection (through torso mask generation). Additionally, we use [rembg](https://github.com/danielgatis/rembg) to effectively remove backgrounds from images.
```
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
```

The process of generating on TensorDock cheap servers with GPU:

<img src="https://github.com/narkov/justai/blob/main/images/inpainting.gif" width=500 /> 

Sample of model before and after replaced outfits

<img src="https://github.com/narkov/justai/blob/main/images/model-man.png" width=100 /> <img src="https://github.com/narkov/justai/blob/main/images/new0.jpg" width=100 /> <img src="https://github.com/narkov/justai/blob/main/images/new.png" width=100 />


### run_animate.py
This script utilizes [First Order Motion Model for Image Animation](https://papers.nips.cc/paper_files/paper/2019/hash/31c0b36aef265d9221af80872ceb62f9-Abstract.html) and its Python [first-order-model](https://github.com/AliaksandrSiarohin/first-order-model) implemenation. It works best with a GPU but can also run on a CPU (though slowly).

#### Setup Steps:
1. Clone the first-order-model repository:
    ```sh
    git clone https://github.com/AliaksandrSiarohin/first-order-model
    cd first-order-model
    ```

2. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```

3. Download checkpoints and template:
    ```sh
    mkdir checkpoints
    cd checkpoints
    download fashion.pth.tar from the provided [google drive link](https://drive.google.com/drive/folders/1PyQJmkdCsAkOYwUyaj_l-l0as-iLDgeH) and place it in the checkpoints directory
    get the animation video e.g. fashion.mov and put in on server
    ```
    
<img src="https://github.com/narkov/justai/blob/main/images/fashion.gif" width=150 />

4. Run the demo script:
    ```sh
    python demo.py --config config/fashion-256.yaml \
        --driving_video fashion.mov \
        --source_image output3.png \
        --checkpoint checkpoints/fashion.pth.tar \
        --relative --adapt_scale --result_video /tmp/result.mp4
    ```

<img src="https://github.com/narkov/justai/blob/main/images/final.gif" width=200 />

### run_final.py
This script uses the moviepy library to compile the final video.

#### Setup Steps:
1. Install dependencies:
    ```sh
    pip install moviepy boto3
    ```

Video output
(https://github.com/MyroslavG/VIDEO-AD-CREATION-TOOL/blob/main/images/result.mp4)   

## Environment Variables
Create a `.env` file to customize the setup:
```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY=xxxx
AWS_SECRET_KEY=xxxx
S3_BUCKET_NAME=outfitai-ad
AMAZON_URL=https://www.amazon.com/Columbia-Powder-Jacket-Black-Large/dp/B07JW4TL96/?th=1
AWS_REGION=us1-west
VoiceId=Joanna
OUTFIT_FILE=jacket.jpg
OUTFIT_NOBG_FILE=jacket-nobg.jpg
MODEL_FILE=model.jpg
MODEL_NOBG_FILE=model-nobg.jpg
MODEL_OUTFIT_FILE=model-outfit.jpg
AUDIO_FILE=audio.mp3
VIDEO_FILE=model.mp4
FINAL_FILE=output.mp4
```

## Future Improvements

1. Integrate AWS Bedrock for run_outfit.py
2. Improve the quality of outfit replacement and animation
3. Implement DB tasks scheduling using the following DB structure

<img src="https://github.com/narkov/justai/blob/main/images/db-str.png" width=150 />

4. Integrate sentry.io for errors/performance logging
