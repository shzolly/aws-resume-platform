import json
import boto3
import uuid
import os
from datetime import datetime, timezone

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    # Extract userId from Cognito JWT claims
    claims = event['requestContext']['authorizer']['jwt']['claims']
    user_id = claims['sub']

    resume_id = str(uuid.uuid4())
    body = json.loads(event.get('body', '{}'))

    item = {
        'userId':    user_id,
        'resumeId':  resume_id,
        'updatedAt': datetime.now(timezone.utc).isoformat(),
        'data':      body.get('data', {})
    }

    table.put_item(Item=item)

    return {
        'statusCode': 201,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'resumeId': resume_id})
    }
