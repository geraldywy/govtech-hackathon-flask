from FaceCropper import FaceCropper
from flask import Flask, render_template, request, redirect, url_for
from flask_cors import CORS, cross_origin
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import time
import logging
import boto3
from botocore.exceptions import ClientError
import requests
from flask import jsonify
# from s3_api import upload_file_to_s3

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

S3_BUCKET = os.environ.get("S3_BUCKET_NAME")
S3_KEY = os.environ.get("S3_ACCESS_KEY")
S3_SECRET = os.environ.get("S3_SECRET_ACCESS_KEY")
S3_LOCATION  = 'http://{}.s3.amazonaws.com/'.format(S3_BUCKET)

app.config["SECRET_KEY"] = os.urandom(32)

ALLOWED_EXTENSIONS = { 'png', 'jpg', 'jpeg' }
# UPLOAD_FOLDER = 'static'



s3 = boto3.client(
   "s3",
   aws_access_key_id=S3_KEY,
   aws_secret_access_key=S3_SECRET
)

GEN_IMAGES_PRESIGNED_URL = "https://1f6mc4zh9j.execute-api.ap-southeast-1.amazonaws.com/testing/images"
CLIENT_FOLDER = "client_pics"
PROCESSED_FOLDER = "processed_pics"

@app.route('/')
def hello_world():
    # url = requests.get(GEN_IMAGES_PRESIGNED_URL).content.decode()
    # print(type(url))
    # print(url)
    # return render_template("load_image.html", image=url)
    # harmless comment, 123
    return "hi"


# display S3 image file
@app.route("/get_pic/<prefix>/<filename>", methods=['GET'])
def get_pic(prefix, filename):
    payload = {
        "object": f"{prefix}/{filename}"
    }
    url = requests.post(GEN_IMAGES_PRESIGNED_URL, json=payload).content.decode()

    return render_template("load_image.html", image=url)



# this method handles processing logic
@app.route("/upload-file", methods=["POST"])
def upload_file():

    if "user_file" not in request.files:
        return "No user_file key in request.files"

    file = request.files["user_file"]

    """
        These attributes are also available

        file.filename               # The actual name of the file
        file.content_type
        file.content_length
        file.mimetype

    """

    if file.filename == "":
        return "Please specify a file"

    if file and allowed_file(file.filename):
        file.filename = secure_filename(file.filename)
        object_key = upload_file_to_s3(file, S3_BUCKET, f"{CLIENT_FOLDER}/{file.filename}")
        s3.download_file(S3_BUCKET, object_key, f"processed-{file.filename}")
        
        # use face cropper here
        cropper = FaceCropper(S3_BUCKET, f"processed-{file.filename}")
        local_file_name = cropper.generate(show_result=False)
        s3.upload_file(local_file_name, S3_BUCKET, f"{PROCESSED_FOLDER}/{local_file_name}")

        payload = {
            "object": f"{PROCESSED_FOLDER}/processed-{file.filename}"
        }
        url = requests.post(GEN_IMAGES_PRESIGNED_URL, json=payload).content.decode()
        return url

    else:
        return "file not allowed"

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# this file name given is local file copy, we overwrite it with the processed image and save
# the processed image to s3 as well
# delete the local copy after to keep this container lean
# when user requests to download, we bring it over from s3 in another method
def process_image(client_file_link):
    time.sleep(5)  # mock response time
    return "https://sagemaker-studio-q6rx2fxnipm.s3-ap-southeast-1.amazonaws.com/cropping_prediction/test.png" # hardcoded for frontend dev

def upload_file_to_s3(file, bucket_name, object_key):
    print("uploading to s3...")
    try:
        s3.upload_fileobj(
            file,
            bucket_name,
            object_key
        )
        print("uploaded to s3")

    except Exception as e:
        print("Error uploading: ", e)
        return e

    return object_key


if __name__ == '__main__':
    app.run(debug=True)