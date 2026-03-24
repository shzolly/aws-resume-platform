import json
import boto3
import os

events_client = boto3.client('events')
EVENT_BUS_NAME = os.environ['EVENT_BUS_NAME']

def lambda_handler(event, context):
    for record in event['Records']:
        # Only process INSERT and MODIFY events
        if record['eventName'] not in ('INSERT', 'MODIFY'):
            continue

        new_image = record['dynamodb'].get('NewImage', {})

        user_id   = new_image.get('userId',   {}).get('S', '')
        resume_id = new_image.get('resumeId', {}).get('S', '')

        if not user_id or not resume_id:
            continue

        # Publish event to EventBridge custom bus
        response = events_client.put_events(
            Entries=[
                {
                    'Source':       'resume.platform',
                    'DetailType':   'ResumeUpdated',
                    'Detail':       json.dumps({
                        'userId':   user_id,
                        'resumeId': resume_id
                    }),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )

        print(f"EventBridge response: {response}")

    return {'statusCode': 200}
