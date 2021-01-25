import requests
import os

GEN_IMAGES_PRESIGNED_URL = os.environ.get("LAMBDA_TO_S3_URL")

def get_file(file_name):
    # request for a new presigned url to the new image in s3 to display to user
    payload = {
        "object": f"{file_name}"
    }
    url = requests.post(GEN_IMAGES_PRESIGNED_URL, json=payload).content.decode()

    return url