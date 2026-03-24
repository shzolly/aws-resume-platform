# AWS Resume Management Platform

A cloud-native Resume Management Platform built as a hands-on project.

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
Covers: Serverless Microservices · Event-Driven Architecture · IaC · GitOps · CDN Hosting · Auto Scaling
