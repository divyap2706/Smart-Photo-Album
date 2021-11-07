import json
import boto3
import requests
import datetime
from requests_aws4auth import AWS4Auth

region = 'us-east-1'
service = 'es'
HOST = "https://search-photoalbumlabel-45itzrcuelgpzinxak4xrjjtou.us-east-1.es.amazonaws.com/"
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
    
def get_customLabel(bucketName, photoName):
    s3 = boto3.client('s3')
    try:
        response = s3.head_object(Bucket=bucketName, Key=photoName)
        customLabels = response['Metadata']['customlabels'].split(', ')
        customLabels = [l.strip().lower() for l in customLabels]
        if len(customLabels) == 0:
            return 
    except:
        return
    
    client = boto3.client('lexv2-models')
    response = client.describe_slot_type(
        slotTypeId='GIXF9DKUYR',
        botId='8D4R2DLNY2',
        botVersion='DRAFT',
        localeId='en_US'
    )
    labels = set([_['sampleValue']['value'] for _ in response['slotTypeValues']])
    N = len(labels)
    labels = labels | set(customLabels)
    if len(labels) != N:
        labels = [{'sampleValue': {'value': l}} for l in labels]
        response = client.update_slot_type(
            slotTypeId='GIXF9DKUYR',
            slotTypeName='keyWords',
            slotTypeValues=labels,
            valueSelectionSetting={
                'resolutionStrategy': 'OriginalValue'
            },
            botId='8D4R2DLNY2',
            botVersion='DRAFT',
            localeId='en_US'
        )
        try:
            response = client.build_bot_locale(
                botId='8D4R2DLNY2',
                botVersion='DRAFT',
                localeId='en_US'
            )
        except: 
            pass    
    return customLabels
    
def uploadES(bucketName, photoName, labels):
    body = {
        'objectKey': photoName,
        'bucket': bucketName,
        'createdTimestamp': datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S"),
        'labels': labels
    }
    query = HOST + 'photos/_doc/'+photoName
    response = requests.post(query, auth=awsauth, data=json.dumps(body), headers={'Content-type': 'application/json'})
    return response

def lambda_handler(event, context):
    print(event)
    s3 = boto3.client('s3')
    bucketName = event["Records"][0]["s3"]["bucket"]["name"]
    photoName = event["Records"][0]["s3"]["object"]["key"]
    customLabels = get_customLabel(bucketName, photoName)
    labels = getLabel(bucketName, photoName)
    if customLabels: labels = list(set(labels+customLabels))
    print(labels)
    response = uploadES(bucketName, photoName, labels)
    print(json.loads(response.text))
    return {
        'statusCode': 200,
        'body': json.loads(response.text)
    }
