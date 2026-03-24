import json
import boto3
import os
import time
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

# ── AWS clients ──────────────────────────────────────────────
sqs      = boto3.client('sqs',      region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-2'))
s3       = boto3.client('s3',       region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-2'))
dynamodb = boto3.resource('dynamodb',region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-2'))

SQS_URL     = os.environ['SQS_QUEUE_URL']
BUCKET_NAME = os.environ['SNAPSHOT_BUCKET']
TABLE_NAME  = os.environ['TABLE_NAME']
table       = dynamodb.Table(TABLE_NAME)


# ── PDF Generation ───────────────────────────────────────────
def generate_pdf(data):
    buffer = BytesIO()
    doc    = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story  = []

    story.append(Paragraph(data.get('name',  'Unknown'), styles['Title']))
    story.append(Paragraph(data.get('title', ''),        styles['Heading2']))
    story.append(Spacer(1, 12))

    if data.get('email'):
        story.append(Paragraph(f"Email: {data['email']}", styles['Normal']))
    if data.get('phone'):
        story.append(Paragraph(f"Phone: {data['phone']}", styles['Normal']))
    story.append(Spacer(1, 12))

    if data.get('summary'):
        story.append(Paragraph('Summary',       styles['Heading3']))
        story.append(Paragraph(data['summary'], styles['Normal']))
        story.append(Spacer(1, 12))

    if data.get('skills'):
        story.append(Paragraph('Skills', styles['Heading3']))
        story.append(Paragraph(', '.join(data['skills']), styles['Normal']))
        story.append(Spacer(1, 12))

    if data.get('experience'):
        story.append(Paragraph('Experience', styles['Heading3']))
        for exp in data['experience']:
            story.append(Paragraph(
                f"{exp.get('role','')} at {exp.get('company','')} "
                f"({exp.get('startDate','')} – {exp.get('endDate','Present')})",
                styles['Heading4']
            ))
            story.append(Paragraph(exp.get('description',''), styles['Normal']))
            story.append(Spacer(1, 8))

    if data.get('education'):
        story.append(Paragraph('Education', styles['Heading3']))
        for edu in data['education']:
            story.append(Paragraph(
                f"{edu.get('degree','')} — "
                f"{edu.get('school','')} ({edu.get('year','')})",
                styles['Normal']
            ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


# ── Message Processing ───────────────────────────────────────
def process_message(msg):
    body      = json.loads(msg['Body'])
    detail    = body.get('detail', body)
    user_id   = detail.get('userId')
    resume_id = detail.get('resumeId')

    print(f"Processing: userId={user_id}, resumeId={resume_id}")

    # Fetch resume from DynamoDB
    response = table.get_item(
        Key={'userId': user_id, 'resumeId': resume_id}
    )
    item = response.get('Item')
    if not item:
        print(f"Resume not found — skipping: {resume_id}")
        return

    data = item.get('data', {})

    # Generate PDF
    pdf_bytes = generate_pdf(data)
    pdf_key   = f"pdfs/{user_id}/{resume_id}.pdf"

    # Upload PDF to S3
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=pdf_key,
        Body=pdf_bytes,
        ContentType='application/pdf'
    )
    print(f"PDF saved: s3://{BUCKET_NAME}/{pdf_key}")

    # Update DynamoDB with PDF key
    table.update_item(
        Key={'userId': user_id, 'resumeId': resume_id},
        UpdateExpression='SET pdfKey = :k, pdfStatus = :s',
        ExpressionAttributeValues={
            ':k': pdf_key,
            ':s': 'generated'
        }
    )
    print(f"DynamoDB updated with pdfKey: {pdf_key}")


# ── Main Polling Loop ────────────────────────────────────────
if __name__ == '__main__':
    print(f"PDFGenerator container started")
    print(f"Queue:  {SQS_URL}")
    print(f"Bucket: {BUCKET_NAME}")
    print(f"Table:  {TABLE_NAME}")

    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=SQS_URL,
                MaxNumberOfMessages=5,
                WaitTimeSeconds=20      # long polling — efficient and cheap
            )
            messages = response.get('Messages', [])

            if not messages:
                print("No messages — waiting...")
                continue

            for msg in messages:
                try:
                    process_message(msg)
                    # Delete on success
                    sqs.delete_message(
                        QueueUrl=SQS_URL,
                        ReceiptHandle=msg['ReceiptHandle']
                    )
                    print(f"Message deleted from queue")
                except Exception as e:
                    print(f"Error processing message: {e}")
                    # Do NOT delete — let it retry up to maxReceiveCount then go to DLQ

        except Exception as e:
            print(f"Queue error: {e}")
            time.sleep(5)
