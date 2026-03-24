import json
import boto3
import os
from datetime import datetime, timezone

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    claims = event['requestContext']['authorizer']['jwt']['claims']
    user_id = claims['sub']
    resume_id = event['pathParameters']['resumeId']
    body = json.loads(event.get('body', '{}'))

    response = table.update_item(
        Key={'userId': user_id, 'resumeId': resume_id},
        UpdateExpression='SET #data = :data, updatedAt = :ts',
        ConditionExpression='userId = :uid',  # ownership check
        ExpressionAttributeNames={'#data': 'data'},
        ExpressionAttributeValues={
            ':data': body.get('data', {}),
            ':ts':   datetime.now(timezone.utc).isoformat(),
            ':uid':  user_id
        },
        ReturnValues='UPDATED_NEW'
    )

    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'updated': True})
    }
