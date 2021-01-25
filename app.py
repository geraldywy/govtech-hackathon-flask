from models import FaceCropper, BackgroundRemover
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
from helper import helper

# load env variables
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

# import model as a class and add in here for the image to run through it
MODELS = [ FaceCropper, BackgroundRemover ]

s3 = boto3.client(
   "s3",
   aws_access_key_id=S3_KEY,
   aws_secret_access_key=S3_SECRET
)



CLIENT_FOLDER = "client_pics"
PROCESSED_FOLDER = "processed_pics"


@app.route("/")
def hello():
    return "hello! 😃"

# display S3 image file
@app.route("/get_pic/<prefix>/<filename>", methods=['GET'])
def get_file(prefix, filename):
    url = helper.get_file(f"{prefix}/{filename}")

    # return render_template("load_image.html", image=url)
    return url

# this method handles processing logic
@app.route("/upload-file", methods=["POST"])
def upload_file():

    if "user_file" not in request.files:
        return "No user_file key in request.files"

    file = request.files["user_file"]

    if file.filename == "":
        return "Please specify a file"

    if file and allowed_file(file.filename):

        # rename the file with random bytes
        split_ext = os.path.splitext(file.filename)
        file.filename = split_ext[0] + "-" + str(os.urandom(8)) + split_ext[1]
        file.filename = secure_filename(file.filename) # randomize the names

        CLIENT_FILE_IN_S3 = f"{CLIENT_FOLDER}/{file.filename}"
        CLIENT_FILE_LOCAL = f"processed-{file.filename}"
        PROCESSED_FILE_IN_S3 = f"{PROCESSED_FOLDER}/{file.filename}"

        # upload original to s3 as well, in case we want to do a feedback loop and also collect client pics
        s3.upload_fileobj(file, S3_BUCKET, CLIENT_FILE_IN_S3)

        # download locally to be ran through models
        s3.download_file(S3_BUCKET, CLIENT_FILE_IN_S3, CLIENT_FILE_LOCAL)

        return process_image(CLIENT_FILE_LOCAL, PROCESSED_FILE_IN_S3)

    else:
        return "file not allowed"

def process_image(local_file, processed_file_in_s3):

    # ensure prerequestites are downloaded
    if not (os.path.exists("resources/u2net.pth") and os.path.exists('resources/u2netp.pth')):
        try:
            os.mkdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources"))
            print("downloading resources file")
            s3.download_file(S3_BUCKET, 'resources/u2net.pth', 'resources/u2net.pth')
            s3.download_file(S3_BUCKET, 'resources/u2netp.pth', 'resources/u2netp.pth')
        except Exception as e:
            return "error downloading resources file: " + e


    # use face cropper here, every model has to overwrite the existing local file
    # we push a final upload to s3 once it runs through every model
    # API of every model
    # 1. instantiated with local file name to target
    # 2. has a generate method which reads and overwrites from the same local file name 
    for model in MODELS:
        instance = model(local_file)
        instance.generate()
    
    # save results, overwriting the s3 file version
    s3.upload_file(local_file, S3_BUCKET, processed_file_in_s3)

    # lastly clean up the local copy to keep this server clean
    os.remove(local_file)

    # request for a new presigned url to the new image in s3 to display to user
    url = helper.get_file(processed_file_in_s3)
    return url

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# expose endpoint
if __name__ == '__main__':
    app.run(host='0.0.0.0')