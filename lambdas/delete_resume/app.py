import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    claims = event['requestContext']['authorizer']['jwt']['claims']
    user_id = claims['sub']
    resume_id = event['pathParameters']['resumeId']

    table.delete_item(
        Key={'userId': user_id, 'resumeId': resume_id},
        ConditionExpression='userId = :uid',  # ownership check
        ExpressionAttributeValues={':uid': user_id}
    )

    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'deleted': True})
    }
