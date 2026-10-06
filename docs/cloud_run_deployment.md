# Deploying Control Plane to Google Cloud Run

This guide outlines how to deploy the FastAPI Control Plane as a secure, containerized, and serverless application on Google Cloud Run.

## Prerequisites
- A Google Cloud Project (`PROJECT_ID`)
- Google Cloud SDK (`gcloud`) authenticated locally
- Artifact Registry enabled (`gcloud services enable artifactregistry.googleapis.com`)
- Cloud Run enabled (`gcloud services enable run.googleapis.com`)

## 1. Build and Push the Docker Image

We use Artifact Registry to store the Docker image.

```bash
# Set environment variables
export PROJECT_ID="meter-to-cash-prod"
export REGION="us-central1"
export REPO_NAME="utility-apps"
export IMAGE_NAME="control-plane"
export IMAGE_TAG="latest"
export FULL_IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${IMAGE_TAG}"

# Create Artifact Registry Repository (run once)
gcloud artifacts repositories create ${REPO_NAME} \
    --repository-format=docker \
    --location=${REGION} \
    --description="Docker repository for utility platform services"

# Build via Google Cloud Build (or build locally and push)
cd backend
gcloud builds submit --tag ${FULL_IMAGE_URL}
```

## 2. Deploy to Cloud Run

We deploy the image to Cloud Run, ensuring environment variables are securely injected via Google Secret Manager.

```bash
gcloud run deploy control-plane-service \
    --image ${FULL_IMAGE_URL} \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --set-env-vars="APP_ENV=production,GCP_REGION=${REGION}" \
    --set-secrets="DATABASE_URL=control_plane_db_url:latest,API_KEY_SECRET=control_plane_api_key:latest" \
    --service-account="control-plane-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 1 \
    --max-instances 10
```

## 3. Key Design Decisions for Cloud Run
- **No Secrets in Source Code**: Database URLs and API secrets are strictly injected via `Secret Manager`.
- **Stateless**: The FastAPI service has no local disk persistence; it interfaces entirely with Cloud SQL (Postgres) and BigQuery.
- **Auto-Scaling**: Scales from 1 to 10 instances based on load, preventing unnecessary costs during idle periods.
- **Service Identity**: Uses a dedicated Service Account (`control-plane-sa`) configured with least-privilege IAM roles (e.g., BigQuery Data Editor, Pub/Sub Publisher).
