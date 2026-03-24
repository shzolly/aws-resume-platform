import json
import boto3
import os
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    resume_id = event['pathParameters']['resumeId']

    # Query GSI — public access, no auth needed
    response = table.query(
        IndexName='resumeId-index',
        KeyConditionExpression=Key('resumeId').eq(resume_id)
    )

    items = response.get('Items', [])
    if not items:
        return {
            'statusCode': 404,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Resume not found'})
        }

    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(items[0], default=str)
    }
