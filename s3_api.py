# import boto3
# from app import s3


# def upload_file(file_name, bucket):
#     """
#     Function to upload a file to an S3 bucket
#     """
#     object_name = file_name
#     s3_client = boto3.client('s3')
#     response = s3_client.upload_file(file_name, bucket, object_name)

#     return response


# def download_file(file_name, bucket):
#     """
#     Function to download a given file from an S3 bucket
#     """
#     s3 = boto3.resource('s3')
#     output = f"downloads/{file_name}"
#     s3.Bucket(bucket).download_file(file_name, output)

#     return output

