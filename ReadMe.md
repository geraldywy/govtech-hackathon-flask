# Hackathon backend flask app

## Project structure
We store all our models in the models directory. API endpoints are all contained within a single file app.py. <br/>
All processing of client's images are done within this application and is uploaded to S3 for storage. <br/>
Images uploaded to S3 cannot be accessed publicly for security purposes. Instead, we retrieve them by generating a presigned url from an AWS lambda endpoint to access an image file stored on S3. This is contained in the helper.py file.

## Spinning up a local instance
1. We have a local dockerfile ready.
2. Additionally, we require a .env file for a few other sensitive variables. Note: The local instance is working with the same S3 bucket as the deployed app.
3. To build the image, run the command `docker build -t <name of your container> .` 
4. To run: `docker run -p 5000:5000 <name of your container>`

## Contribution guide
TBD

## CI/CD
We are using github workflow to automate deployment on Azure app service. All changes to master branch will be automatically reflected on the deployed app: https://passport-crop.azurewebsites.net/ <br/>
The full details of the flow is contained in the workflow yaml file.

