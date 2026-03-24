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

CI/CD
  └── Jenkins (on EKS)
        ├── pytest → sam build → sam deploy (CloudFormation)
        ├── docker build → ECR push
        └── Update k8s-manifests repo → ArgoCD syncs to EKS
```

---

## 5 Architectural Pillars

| Pillar | Services |
|---|---|
| 1. CRUD Microservice | API Gateway, Lambda, DynamoDB, Cognito |
| 2. Event-Driven | DynamoDB Streams, EventBridge, SQS, SNS, Lambda |
| 3. CI/CD Deployment | Jenkins, CloudFormation/SAM, Amazon EKS |
| 4. GitOps | GitHub, ArgoCD, ECR |
| 5. Static Hosting | S3, CloudFront, ACM, Route 53 |

---

## Repository Structure

```
aws-resume-platform/
├── template.yaml                  # SAM / CloudFormation (all infrastructure)
├── samconfig.toml                 # SAM deploy defaults
├── Jenkinsfile                    # CI/CD pipeline definition
├── lambdas/
│   ├── create_resume/app.py       # POST /resume
│   ├── get_resume/app.py          # GET  /resume/{resumeId} (public)
│   ├── update_resume/app.py       # PUT  /resume/{resumeId}
│   ├── delete_resume/app.py       # DELETE /resume/{resumeId}
│   ├── list_resumes/app.py        # GET  /resumes
│   ├── fanout_handler/app.py      # DynamoDB Stream → EventBridge
│   └── pdf_generator/
│       ├── app.py                 # Lambda version (JSON snapshot)
│       └── requirements.txt
├── pdf-generator-container/
│   ├── app.py                     # EKS container version (real PDF)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend2/
│   ├── index.html                 # Login / Register
│   ├── dashboard.html             # Owner resume list
│   ├── editor.html                # Resume editor
│   ├── view.html                  # Public resume viewer (no auth)
│   └── config.js                  # AWS config values (fill before deploy)
└── tests/
    └── test_lambdas.py            # Unit tests (pytest)
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
