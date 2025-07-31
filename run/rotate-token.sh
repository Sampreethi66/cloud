#!/bin/bash

# 🔄 Rotate shared UI access token used by frontend & backend
# Updates .env, builds Docker image, and re-deploys to Cloud Run

set -e

ENV_FILE=".env"
CONFIG_FILE="config.yaml"
TOKEN_VAR="UI_ACCESS_TOKEN"

# --- Step 1: Check for .env file
if [ ! -f "$ENV_FILE" ]; then
  echo "❌ .env file not found. Aborting."
  exit 1
fi

# --- Step 2: Generate new 32-char token
NEW_TOKEN=$(openssl rand -hex 16)

# --- Step 3: Update token in .env
if grep -q "^${TOKEN_VAR}=" "$ENV_FILE"; then
  sed -i.bak "s/^${TOKEN_VAR}=.*/${TOKEN_VAR}=${NEW_TOKEN}/" "$ENV_FILE"
else
  echo "${TOKEN_VAR}=${NEW_TOKEN}" >> "$ENV_FILE"
fi
echo "✅ Updated ${TOKEN_VAR} in .env"

# --- Step 4: Load .env into shell
set -a
source "$ENV_FILE"
set +a

# --- Step 5: Load missing vars from config.yaml
eval $(python3 -c "
import yaml
with open('$CONFIG_FILE') as f:
    config = yaml.safe_load(f)
print(f'SERVICE_NAME=\"{config.get(\"service\", {}).get(\"name\", \"\")}\"')
print(f'GOOGLE_CLOUD_REGION=\"{config.get(\"project\", {}).get(\"region\", \"\")}\"')
print(f'IMAGE_NAME=\"{config.get(\"container\", {}).get(\"image_name\", \"notebook-executor\")}\"')
")

# Fall back if IMAGE_TAG isn't explicitly set
IMAGE_TAG="${IMAGE_TAG:-$IMAGE_NAME}"

# --- Step 6: Check for required values
if [[ -z "$GOOGLE_CLOUD_PROJECT" || -z "$SERVICE_NAME" || -z "$GOOGLE_CLOUD_REGION" || -z "$IMAGE_TAG" ]]; then
  echo "❌ Missing required variables."
  echo "  GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT"
  echo "  SERVICE_NAME=$SERVICE_NAME"
  echo "  GOOGLE_CLOUD_REGION=$GOOGLE_CLOUD_REGION"
  echo "  IMAGE_TAG=$IMAGE_TAG"
  exit 1
fi

# --- Step 7: Build image
echo "🔨 Building Docker image..."
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/$IMAGE_TAG

# --- Step 8: Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/$IMAGE_TAG \
  --platform managed \
  --region "$GOOGLE_CLOUD_REGION" \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,UI_ACCESS_TOKEN=$UI_ACCESS_TOKEN"

echo "✅ Token rotated and redeployed!"
echo "🔑 New UI_ACCESS_TOKEN: $UI_ACCESS_TOKEN"
