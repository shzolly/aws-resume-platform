# AWS Resume Management Platform

A cloud-native Resume Management Platform built as a hands-on project.

## What This Platform Does

The **AWS Resume Management Platform** is a full-stack, cloud-native web application that allows professionals to create, manage, and share their resumes online. It is intentionally kept simple in application logic so the focus remains on demonstrating AWS architectural patterns rather than complex business features.

### Core Functions

| Function | Description |
|---|---|
| **Register / Login** | Users sign up and authenticate using **Amazon Cognito**. Each user receives a JWT token containing a unique `sub` claim that becomes their identity across all AWS services. |
| **Create Resume** | An authenticated owner submits resume data (name, title, skills, experience, education) via a REST API. **API Gateway** validates the JWT, routes the request to a **Lambda** function, which stores the data as a single JSON item in **DynamoDB**. |
| **Edit Resume** | The owner can update any field of their resume at any time. A **conditional write** in DynamoDB ensures only the rightful owner can modify their own record. |
| **Delete Resume** | The owner can permanently delete a resume. An ownership check is enforced at the Lambda level using the Cognito `sub` claim. |
| **List Resumes** | The owner can view all resumes they have created, returned as a lightweight list with name and last-updated timestamp. |
| **Public Resume View** | Anyone with a resume URL can view it — no login required. The public viewer calls a dedicated **unauthenticated API route** that looks up the resume by `resumeId` via a DynamoDB **Global Secondary Index (GSI)**. |
| **Automatic PDF Generation** | Every time a resume is created or updated, **DynamoDB Streams** captures the change and triggers a **FanOutHandler Lambda**, which publishes a `ResumeUpdated` event to **EventBridge**. This fans out to an **SQS queue**, which triggers a **PDFGenerator** — available as both a Lambda function and an **EKS container** — that generates a real PDF using `reportlab` and stores it in **S3**. |
| **Email Notification** | When a resume is updated, **EventBridge** simultaneously routes the event to an **SNS topic**, which sends an email notification to the owner confirming their resume was saved successfully. |
| **Static Web Interface** | A minimal HTML/JavaScript single-page application is hosted on a private **S3 bucket** and served globally over HTTPS via **Amazon CloudFront** with **Origin Access Control (OAC)** — the S3 bucket is never directly accessible. |

## Architecture Overview

```
Browser (HTTPS)
  └── CloudFront (CDN + HTTPS)
        ├── S3 (static frontend)
        └── API Gateway (REST API)
              └── Lambda (CRUD microservices)
                    ├── DynamoDB (data store)
                    └── Cognito (identity + JWT auth)

DynamoDB Streams
  └── FanOutHandler Lambda
        └── EventBridge (custom bus: resume-events)
              ├── SQS → PDFGenerator Lambda → S3 (JSON snapshot)
              ├── SQS → EKS PDFGenerator Container → S3 (real PDF)
              └── SNS → Email notification to owner

Docker microservice
  └── Docker (on ECS)
        ├── ECR → Repository → build, tag and push
        └── ECS → Task and cluster service
```

---

## 5 Architectural Pillars

| Pillar | Services |
|---|---|
| 1. CRUD Microservice | API Gateway, Lambda, DynamoDB, Cognito |
| 2. Event-Driven | DynamoDB Streams, EventBridge, SQS, SNS, Lambda |
| 3. Containerization | ECR, ECS |
| 4. Static Hosting | S3, CloudFront |

---

## Repository Structure

```
aws-resume-platform/
├── lambdas/
│   ├── create_resume/app.py       # POST /resume
│   ├── get_resume/app.py          # GET  /resume/{resumeId} (public)
│   ├── update_resume/app.py       # PUT  /resume/{resumeId}
│   ├── delete_resume/app.py       # DELETE /resume/{resumeId}
│   ├── list_resumes/app.py        # GET  /resumes
│   ├── fanout_handler/app.py      # DynamoDB Stream → EventBridge
│   └── pdf_generator/app.py       # Lambda version (JSON snapshot)
├── pdf-generator-container/
│   ├── app.py                     # ECS container version
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                      # v1
│   ├── index.html                 # Login / Register
│   ├── dashboard.html             # Owner resume list
│   ├── editor.html                # Resume editor
│   ├── view.html                  # Public resume viewer (no auth)
│   └── config.js                  # AWS config values (fill before deploy)
└── frontend2/                     # v2
    ├── index.html                 # Login / Register
    ├── dashboard.html             # Owner resume list
    ├── editor.html                # Resume editor
    ├── view.html                  # Public resume viewer (no auth)
    ├── style.css                  # style
    └── config.js                  # AWS config values (fill before deploy)
```

---

## DynamoDB Schema

**Table:** `Resumes`

| Attribute | Type | Role |
|---|---|---|
| `userId` | String (PK) | Cognito `sub` claim |
| `resumeId` | String (SK) | UUID generated on create |
| `updatedAt` | String | ISO timestamp |
| `pdfKey` | String | S3 key of generated PDF |
| `pdfStatus` | String | `generated` once PDF is ready |
| `data` | Map | Resume content (name, title, skills, etc.) |

**GSI:** `resumeId-index` — enables public lookup by `resumeId` alone (no `userId` needed).

---

## API Endpoints

| Method | Route | Auth | Description |
|---|---|---|---|
| POST | `/resume` | Cognito JWT | Create new resume |
| GET | `/resume/{resumeId}` | None | Public read |
| PUT | `/resume/{resumeId}` | Cognito JWT | Update resume |
| DELETE | `/resume/{resumeId}` | Cognito JWT | Delete resume |
| GET | `/resumes` | Cognito JWT | List owner's resumes |

---

## Author

Built as a hands-on demo project.  
Covers: Serverless Microservices · Event-Driven Architecture · IaC · CI/CD · CDN Hosting · Auto Scaling
