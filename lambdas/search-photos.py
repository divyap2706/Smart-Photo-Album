import json
import boto3
import requests
import datetime
from requests_aws4auth import AWS4Auth

region = 'us-east-1'
service = 'es'
URL = "https://search-photoalbumlabel-45itzrcuelgpzinxak4xrjjtou.us-east-1.es.amazonaws.com/_search"
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

def getLabels(msg):
    client = boto3.client('lexv2-runtime')
    response = client.recognize_text(
        botId = '8D4R2DLNY2',
        botAliasId = 'TSTALIASID',
        localeId = 'en_US',
        sessionId = 'test',
        text = msg
    )
    
    labels = []
    for keyWord in response['sessionState']['intent']['slots']['keyWord']['values']:
        for label in keyWord['value']['resolvedValues']:
            labels.append(label)
            
    return labels
    
def searchES(labels):
    query = {"size":1000 ,"query": {"match": {"labels": " ".join(labels)}}}
    response = requests.post(URL, auth=awsauth, data=json.dumps(query), headers={"Content-Type":"application/json"})
    photos = [photo["_source"] for photo in json.loads(response.text)['hits']['hits']]
    return photos

def lambda_handler(event, context):
    print(event)
    msg = event['queryStringParameters']['q']
    labels = getLabels(msg)
    photos = searchES(labels)
    print(photos)
    return {
        'statusCode': 200,
        'body': json.dumps(photos),
        'headers': {
            'Access-Control-Allow-Headers' : 'Content-Type,X-Amz-Date,X-Amz-Security-Token,Authorization,X-Api-Key,X-Requested-With,Accept,Access-Control-Allow-Methods,Access-Control-Allow-Origin,Access-Control-Allow-Headers',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT'
        },
    }
