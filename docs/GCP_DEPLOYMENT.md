# 🚀 TwinSpark Chronicles - GCP Deployment Guide

## Recommended Architecture

### Database: **Cloud SQL for PostgreSQL**

```
┌─────────────────────────────────────────────┐
│         TwinSpark Chronicles on GCP         │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐      ┌─────────────────┐│
│  │  Cloud Run   │◄────►│  Cloud SQL      ││
│  │  (FastAPI)   │      │  (PostgreSQL)   ││
│  └──────────────┘      └─────────────────┘│
│         ▲                                   │
│         │                                   │
│  ┌──────────────┐      ┌─────────────────┐│
│  │ Cloud Storage│      │  Vertex AI      ││
│  │ (Photos/     │      │  (Gemini API)   ││
│  │  Audio)      │      └─────────────────┘│
│  └──────────────┘                          │
│                                             │
│  ┌─────────────────────────────────────┐  │
│  │     Cloud CDN + Load Balancer       │  │
│  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

---

## 1. Database Setup: Cloud SQL PostgreSQL

### Why Cloud SQL for PostgreSQL?

✅ **Fully Managed** - Automatic backups, patches, high availability  
✅ **ACID Compliance** - Critical for child profiles and story history  
✅ **JSON Support** - PostgreSQL JSONB for flexible metadata  
✅ **Scalability** - Easy vertical scaling (CPU/RAM)  
✅ **Security** - Encryption at rest and in transit  
✅ **Point-in-Time Recovery** - Protect family memories  
✅ **Cost-Effective** - Pay-as-you-go, can start small  

### Instance Recommendations

#### Development/Testing
```
Machine Type: db-f1-micro (0.6 GB RAM)
Storage: 10 GB SSD
Cost: ~$10/month
```

#### Production (Small - 100 users)
```
Machine Type: db-n1-standard-1 (3.75 GB RAM)
Storage: 20 GB SSD
High Availability: Yes (recommended)
Automated Backups: Daily
Cost: ~$70-90/month
```

#### Production (Medium - 1000 users)
```
Machine Type: db-n1-standard-2 (7.5 GB RAM)
Storage: 50 GB SSD
High Availability: Yes
Automated Backups: Daily
Read Replicas: 1 (optional)
Cost: ~$150-200/month
```

---

## 2. Setup Instructions

### Step 1: Create Cloud SQL Instance

```bash
# Set project variables
export PROJECT_ID="twinspark-chronicles"
export REGION="us-central1"
export DB_INSTANCE="twinspark-db"
export DB_NAME="twinspark"
export DB_USER="twinspark_app"

# Create Cloud SQL instance
gcloud sql instances create $DB_INSTANCE \
  --database-version=POSTGRES_15 \
  --tier=db-n1-standard-1 \
  --region=$REGION \
  --storage-type=SSD \
  --storage-size=20GB \
  --storage-auto-increase \
  --backup \
  --backup-start-time=02:00 \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=03 \
  --enable-bin-log \
  --availability-type=REGIONAL
```

### Step 2: Create Database and User

```bash
# Create database
gcloud sql databases create $DB_NAME \
  --instance=$DB_INSTANCE

# Create user
gcloud sql users create $DB_USER \
  --instance=$DB_INSTANCE \
  --password=$(openssl rand -base64 32)
```

### Step 3: Configure Connection

```bash
# Get connection name
gcloud sql instances describe $DB_INSTANCE \
  --format="value(connectionName)"

# Output: PROJECT_ID:REGION:INSTANCE_NAME
# Example: twinspark-chronicles:us-central1:twinspark-db
```

### Step 4: Update Application Configuration

Create `.env.production`:

```bash
# Database Configuration
DB_CONNECTION_NAME="twinspark-chronicles:us-central1:twinspark-db"
DB_NAME="twinspark"
DB_USER="twinspark_app"
DB_PASSWORD="<generated-password>"
DB_HOST="/cloudsql/twinspark-chronicles:us-central1:twinspark-db"  # Unix socket
DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${DB_CONNECTION_NAME}"

# For Cloud Run with Cloud SQL Proxy
USE_CLOUD_SQL_PROXY=true

# Application
ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Gemini AI
GEMINI_API_KEY="<your-api-key>"

# Cloud Storage
GCS_BUCKET="twinspark-media"
GCS_PROJECT_ID="twinspark-chronicles"
```

---

## 3. Application Configuration Updates

### Update `src/config.py`:

```python
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Environment
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./twinspark.db")
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    
    # Cloud SQL
    USE_CLOUD_SQL_PROXY: bool = os.getenv("USE_CLOUD_SQL_PROXY", "false").lower() == "true"
    DB_CONNECTION_NAME: str = os.getenv("DB_CONNECTION_NAME", "")
    
    # Gemini AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Cloud Storage
    GCS_BUCKET: str = os.getenv("GCS_BUCKET", "")
    GCS_PROJECT_ID: str = os.getenv("GCS_PROJECT_ID", "")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### Update `src/utils/database.py` for Cloud SQL:

```python
def __init__(self, database_url: Optional[str] = None):
    """
    Initialize database connection.
    Supports SQLite (dev) and PostgreSQL (Cloud SQL).
    """
    if database_url is None:
        # Check environment
        database_url = os.getenv("DATABASE_URL", "sqlite:///./data/twinspark.db")
    
    self.database_url = database_url
    
    # Engine configuration based on database type
    if database_url.startswith("sqlite"):
        # SQLite configuration (development)
        self.engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )
    else:
        # PostgreSQL configuration (production)
        pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
        pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        
        self.engine = create_engine(
            database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,   # Recycle connections after 1 hour
            echo=False
        )
    
    # Create session factory
    self.SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=self.engine
    )
    
    print(f"💾 Database initialized: {database_url.split('@')[0]}@***")
```

---

## 4. Deploy to Cloud Run

### Step 1: Create Dockerfile

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY frontend/dist/ ./frontend/dist/

# Expose port
EXPOSE 8080

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Step 2: Build and Deploy

```bash
# Build container
gcloud builds submit --tag gcr.io/$PROJECT_ID/twinspark-app

# Deploy to Cloud Run with Cloud SQL connection
gcloud run deploy twinspark-chronicles \
  --image gcr.io/$PROJECT_ID/twinspark-app \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${DB_CONNECTION_NAME}" \
  --set-env-vars "GEMINI_API_KEY=${GEMINI_API_KEY}" \
  --set-env-vars "ENV=production" \
  --add-cloudsql-instances $DB_CONNECTION_NAME \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --concurrency 80 \
  --min-instances 1 \
  --max-instances 10
```

---

## 5. Database Migration with Alembic

### Initialize Alembic (already done)

```bash
# Install alembic
pip install alembic

# Generate migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

### Production Migration

```bash
# Set DATABASE_URL to Cloud SQL
export DATABASE_URL="postgresql://user:pass@/dbname?host=/cloudsql/..."

# Run migration
alembic upgrade head
```

---

## 6. Monitoring and Maintenance

### Cloud SQL Insights

```bash
# Enable Query Insights
gcloud sql instances patch $DB_INSTANCE \
  --insights-config-query-insights-enabled \
  --insights-config-query-string-length=1024 \
  --insights-config-record-application-tags \
  --insights-config-record-client-address
```

### Backups

```bash
# List backups
gcloud sql backups list --instance=$DB_INSTANCE

# Create on-demand backup
gcloud sql backups create --instance=$DB_INSTANCE

# Restore from backup
gcloud sql backups restore <BACKUP_ID> \
  --backup-instance=$DB_INSTANCE \
  --backup-id=<BACKUP_ID>
```

### Performance Tuning

```sql
-- PostgreSQL configuration (via Cloud Console or gcloud)
-- Recommended settings for 1000 concurrent users:

max_connections = 100
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 10MB
min_wal_size = 1GB
max_wal_size = 4GB
```

---

## 7. Cost Optimization

### Development
- Use SQLite locally (free)
- Use Cloud SQL db-f1-micro for testing (~$10/month)
- Delete test instances when not in use

### Production
- Start with db-n1-standard-1
- Enable auto-scaling storage
- Use committed use discounts (save 30%)
- Monitor with Cloud Monitoring (free tier)
- Set up budget alerts

### Estimated Monthly Costs

```
Startup (< 100 users):
- Cloud SQL: $70-90
- Cloud Run: $10-20
- Cloud Storage: $5-10
- Vertex AI (Gemini): $50-100
Total: ~$135-220/month

Growth (1000 users):
- Cloud SQL: $150-200
- Cloud Run: $50-100
- Cloud Storage: $20-30
- Vertex AI (Gemini): $200-500
Total: ~$420-830/month
```

---

## 8. Security Best Practices

### Cloud SQL Security

```bash
# Enable SSL
gcloud sql instances patch $DB_INSTANCE \
  --require-ssl

# Set authorized networks (for external access)
gcloud sql instances patch $DB_INSTANCE \
  --authorized-networks=<YOUR_IP>/32

# Use IAM authentication
gcloud sql users create [EMAIL]@[DOMAIN] \
  --instance=$DB_INSTANCE \
  --type=CLOUD_IAM_USER
```

### Secret Management

```bash
# Store secrets in Secret Manager
echo -n "your-db-password" | gcloud secrets create db-password --data-file=-
echo -n "your-gemini-key" | gcloud secrets create gemini-api-key --data-file=-

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding db-password \
  --member=serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

---

## 9. Alternative: Firestore (NoSQL)

### When to Use Firestore

✅ Serverless architecture  
✅ Global distribution  
✅ Real-time updates  
✅ Lower initial costs  

❌ Complex joins (use Cloud SQL instead)  
❌ Transactions across documents  
❌ Full-text search  

### Firestore Cost Comparison

```
Firestore Pricing (approximate):
- Storage: $0.18/GB/month
- Read operations: $0.06 per 100K
- Write operations: $0.18 per 100K

For 1000 users with 100 sessions/month:
- Storage: ~5GB = $0.90
- Reads: ~1M = $0.60
- Writes: ~500K = $0.90
Total: ~$2.40/month + Vertex AI costs

Much cheaper, but limited query capabilities!
```

---

## 10. Recommendation Summary

### ✅ Use Cloud SQL PostgreSQL if:
- Need complex queries and joins
- Want ACID transactions
- Require relational data integrity
- Planning to scale to 10K+ users
- Need SQL analytics and reporting

### ⚠️ Consider Firestore if:
- Building serverless/mobile-first
- Need global distribution
- Budget is very limited
- Can redesign for NoSQL patterns
- Real-time updates are critical

---

## 🎯 Final Recommendation

**Start with Cloud SQL PostgreSQL** because:

1. ✅ Already implemented in `database.py`
2. ✅ Better for complex relationships (children, traits, sessions, universe)
3. ✅ Easier migration path (SQLite → PostgreSQL)
4. ✅ Better analytics and reporting
5. ✅ Industry standard for this type of application

**Migration Path:**
1. **Month 1-3**: SQLite (local development)
2. **Month 4-6**: Cloud SQL db-n1-standard-1 (production)
3. **Month 7+**: Scale vertically or add read replicas as needed

---

## Need Help?

- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
- [SQLAlchemy with Cloud SQL](https://cloud.google.com/sql/docs/postgres/connect-instance-cloud-run)
