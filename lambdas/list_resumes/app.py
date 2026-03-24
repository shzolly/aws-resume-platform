import json
import boto3
import os
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    claims = event['requestContext']['authorizer']['jwt']['claims']
    user_id = claims['sub']

    response = table.query(
        KeyConditionExpression=Key('userId').eq(user_id)
    )

    items = response.get('Items', [])
    # Return only metadata, not full data blob
    result = [
        {
            'resumeId':  item['resumeId'],
            'updatedAt': item.get('updatedAt', ''),
            'name':      item.get('data', {}).get('name', 'Untitled')
        }
        for item in items
    ]

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*', 
            'Access-Control-Allow-Methods': 'GET,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization'},
        'body': json.dumps(result, default=str)
    }
