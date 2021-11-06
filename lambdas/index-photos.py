import json
import boto3
import requests
import datetime
from requests_aws4auth import AWS4Auth

region = 'us-east-1'
service = 'es'
HOST = "https://search-photos-gv3dffs4hvpuyc6i5am4xfxm5i.us-east-1.es.amazonaws.com/"
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

def getLabel(bucketName, photoName):
    client=boto3.client('rekognition')
    response = client.detect_labels(
        Image = {
            'S3Object': {
                'Bucket': bucketName,
                'Name': photoName
            }
        },
        MinConfidence = 95
    )
    labels = [label['Name'] for label in response['Labels']]
    return labels
    
def uploadES(bucketName, photoName, labels):
    body = {
        'objectKey': photoName,
        'bucket': bucketName,
        'createdTimestamp': datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S"),
        'labels': labels
    }
    query = HOST + 'photos/_doc'
    response = requests.post(query, auth=awsauth, data=json.dumps(body), headers={'Content-type': 'application/json'})
    return response

def lambda_handler(event, context):
    print(event)
    bucketName = event["Records"][0]["s3"]["bucket"]["name"]
    photoName = event["Records"][0]["s3"]["object"]["key"]
    labels = getLabel(bucketName, photoName)
    print(labels)
    response = uploadES(bucketName, photoName, labels)
    print(json.loads(response.text))
    return {
        'statusCode': 200,
        'body': json.loads(response.text)
    }
