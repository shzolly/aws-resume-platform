import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

TABLE_NAME  = os.environ['TABLE_NAME']
BUCKET_NAME = os.environ['SNAPSHOT_BUCKET']

table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    for record in event['Records']:
        # SQS message body is the EventBridge event detail
        body = json.loads(record['body'])

        # EventBridge wraps the detail in a 'detail' key
        detail    = body.get('detail', body)
        user_id   = detail.get('userId')
        resume_id = detail.get('resumeId')

        if not user_id or not resume_id:
            print(f"Missing userId or resumeId in message: {body}")
            continue

        # Fetch resume from DynamoDB
        response = table.get_item(
            Key={'userId': user_id, 'resumeId': resume_id}
        )
        item = response.get('Item')

        if not item:
            print(f"Resume not found: userId={user_id}, resumeId={resume_id}")
            continue

        # Write JSON snapshot to S3
        s3_key = f"snapshots/{user_id}/{resume_id}.json"
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(item, default=str),
            ContentType='application/json'
        )

        print(f"Snapshot saved: s3://{BUCKET_NAME}/{s3_key}")

    return {'statusCode': 200}
