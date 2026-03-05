#!/bin/bash

# TwinSpark Chronicles - GCP Deployment Script
# This script deploys the application to Google Cloud Platform

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║         🚀 TWINSPARK CHRONICLES - GCP DEPLOYMENT             ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if required tools are installed
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install: https://cloud.google.com/sdk/docs/install${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker Desktop${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites OK${NC}\n"

# Load environment variables
if [ ! -f ".env.production" ]; then
    echo -e "${RED}❌ .env.production not found${NC}"
    echo -e "${YELLOW}Please create .env.production from .env.production.example${NC}"
    exit 1
fi

source .env.production

# Verify required variables
REQUIRED_VARS=("PROJECT_ID" "REGION" "SERVICE_NAME" "DB_CONNECTION_NAME")
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}❌ Missing required variable: $var${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ Environment variables loaded${NC}\n"

# Set defaults
PROJECT_ID=${PROJECT_ID:-"twinspark-chronicles"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME=${SERVICE_NAME:-"twinspark-chronicles"}
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo -e "${BLUE}📦 Deployment Configuration:${NC}"
echo "   Project ID: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Service: $SERVICE_NAME"
echo "   Image: $IMAGE_NAME"
echo ""

# Confirm deployment
read -p "$(echo -e ${YELLOW}Continue with deployment? [y/N]:${NC} )" -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Deployment cancelled${NC}"
    exit 1
fi

# Set GCP project
echo -e "\n${YELLOW}🔧 Setting GCP project...${NC}"
gcloud config set project $PROJECT_ID

# Build container
echo -e "\n${YELLOW}🏗️  Building Docker image...${NC}"
gcloud builds submit --tag $IMAGE_NAME --timeout=20m

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Build successful${NC}"

# Deploy to Cloud Run
echo -e "\n${YELLOW}🚀 Deploying to Cloud Run...${NC}"

gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "^||^DATABASE_URL=$DATABASE_URL||GOOGLE_API_KEY=$GOOGLE_API_KEY||APP_ENV=production||DEBUG=false" \
  --add-cloudsql-instances $DB_CONNECTION_NAME \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --concurrency 80 \
  --min-instances 1 \
  --max-instances 10 \
  --port 8080

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Deployment successful!${NC}"

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                               ║${NC}"
echo -e "${GREEN}║                  🎉 DEPLOYMENT COMPLETE!                      ║${NC}"
echo -e "${GREEN}║                                                               ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo -e "\n${BLUE}📍 Service URL:${NC} $SERVICE_URL"
echo -e "${BLUE}🔍 View logs:${NC} gcloud run logs tail $SERVICE_NAME --region $REGION"
echo -e "${BLUE}📊 Console:${NC} https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME"
echo ""

# Run database migrations (optional)
read -p "$(echo -e ${YELLOW}Run database migrations? [y/N]:${NC} )" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n${YELLOW}🔄 Running database migrations...${NC}"
    # You'll need to set up Cloud SQL proxy for this
    # Or run migrations from a Cloud Run job
    echo -e "${YELLOW}⚠️  Please run migrations manually:${NC}"
    echo "   1. Install Cloud SQL proxy"
    echo "   2. Set DATABASE_URL environment variable"
    echo "   3. Run: alembic upgrade head"
fi

echo -e "\n${GREEN}✨ All done! Your app is live at: $SERVICE_URL${NC}\n"
