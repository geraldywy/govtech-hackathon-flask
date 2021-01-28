from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import boto3
from helper import helper
from flask_api import status

from models import FaceCropper, BackgroundRemover, Centralize, SmileDetector, AutoTransform

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

ALLOWED_EXTENSIONS = { 'png', 'jpg', 'jpeg', 'jfif', 'jpe', 'jif', 'jfi', 'webp' }

# import model as a class and add in here for the image to run through it
MODELS = [  AutoTransform, BackgroundRemover  ]
DETECTORS = [ SmileDetector ]
PRE_REQ = ['resources/u2net.pth', 'resources/u2netp.pth', 'resources/shape_predictor_68_face_landmarks.dat', 'resources/smile.hdf5', 'resources/singapore-passport-photo.jpg']


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

# get a presigned url to access an S3 file
@app.route("/get_pic/<prefix>/<filename>", methods=['GET'])
def get_file(prefix, filename):
    url = helper.get_file(f"{prefix}/{filename}")
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
        file.filename = secure_filename(file.filename)

        CLIENT_FILE_IN_S3 = f"{CLIENT_FOLDER}/{file.filename}"
        CLIENT_FILE_LOCAL = f"processed-{file.filename}"
        PROCESSED_FILE_IN_S3 = f"{PROCESSED_FOLDER}/{file.filename}"

        try:
            s3.upload_fileobj(file, S3_BUCKET, CLIENT_FILE_IN_S3)
        except:
            return f"Error uploading: {file.filename} to bucket: {S3_BUCKET} as object: {CLIENT_FILE_IN_S3}"
        try:
            # download locally to be ran through models
            s3.download_file(S3_BUCKET, CLIENT_FILE_IN_S3, CLIENT_FILE_LOCAL)
        except:
            return f"Error downloading client file"

        
        processed_image_url = process_image(CLIENT_FILE_LOCAL, PROCESSED_FILE_IN_S3)
        issues = check_issues(CLIENT_FILE_LOCAL)

        details = {
            "image_url": processed_image_url,
            "issues": issues
        }

        # remove the local file once done
        os.remove(CLIENT_FILE_LOCAL)
        return jsonify(details)

    else:
        return "Illegal file extension", status.HTTP_400_BAD_REQUEST

def process_image(local_file, processed_file_in_s3):

    if not ensure_prereq():
        return "Failed loading in pre-req resources", status.HTTP_503_SERVICE_UNAVAILABLE

    # API of every model
    # 1. instantiated with local file name to target
    # 2. has a generate method which reads and overwrites from the same local file name 
    for model in MODELS:
        instance = model(local_file)
        # try:
        instance.generate()
    # except Exception as e:
        # print("Failed for", instance.model_name, "Error: ", str(e))
    
    # save results, overwriting the s3 file version
    s3.upload_file(local_file, S3_BUCKET, processed_file_in_s3)

    # request for a new presigned url to the new image in s3 to display to user
    url = helper.get_file(processed_file_in_s3)
    return url

def check_issues(local_file):
    issues = []
    # run through the detectors model here
    for detector in DETECTORS:
        detector_instance = detector()
        try:
            warning_message = detector_instance.detect(local_file)
            if warning_message:
                issues.append(warning_message)
        except Exception as e:
            print("failed for", detector_instance.name, "Error:", e)
    
    return issues

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def ensure_prereq():
    # ensure prerequestites are downloaded
    for req in PRE_REQ:
        if not os.path.exists(req):
            try:
                if not os.path.isdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources")):
                    os.mkdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources"))
                s3.download_file(S3_BUCKET, req, req)
            except Exception as e:
                return False
    
    return True


# expose endpoint
if __name__ == '__main__':
    app.run(host='0.0.0.0')



    