from flask import Flask, render_template, request, redirect, url_for
from flask_cors import CORS, cross_origin
import os
from werkzeug.utils import secure_filename
from s3_api import *
from dotenv import load_dotenv
import time

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


@app.route('/')
def hello_world():
    return "hello :)"

# this method has to handle the coordination logic to save an image and direct the process end point to return us the processed image link
# 1. client posts with an image file, we save in s3
# 2. pass the client s3 pic link into the process method
# 3. some backend magic happens, we store the processed image into s3 again
# 4. return client app the processed s3 url
@app.route("/", methods=["POST"])
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
        filename = secure_filename(file.filename)
        client_file_link = upload_file_to_s3(file, S3_BUCKET)
        return process_image(client_file_link)

    else:
        return "file not allowed"


def upload_file_to_s3(file, bucket_name, acl="public-read"):
    print("uploading to s3...")
    try:
        s3.upload_fileobj(
            file,
            bucket_name,
            file.filename,
            ExtraArgs={
                "ACL": acl,
                "ContentType": file.content_type
            }
        )
        print("uploaded to s3")

    except Exception as e:
        print("Error uploading: ", e)
        return e

    return "{}{}".format(S3_LOCATION, file.filename)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# need to invoke aws api gateway sagemaker endpoint
# this activates a sagemaker notebook to process the s3 link given
# and saves the output file into s3, returns us the processed image link
def process_image(client_file_link):
    time.sleep(5)  # mock response time
    return "https://sagemaker-studio-q6rx2fxnipm.s3-ap-southeast-1.amazonaws.com/cropping_prediction/test.png" # hardcoded for frontend dev




if __name__ == '__main__':
    app.run(debug=True)