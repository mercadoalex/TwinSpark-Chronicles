"""
TwinSpark Chronicles - Main Application

Entry point for the TwinSpark Chronicles interactive storytelling system.
"""

import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings

# Setup logging - FIX: Use UPPERCASE
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),  # Convert to uppercase
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Import the FastAPI app
from api.session_manager import app
from fastapi.staticfiles import StaticFiles
from api.dashboard_routes import router as dashboard_router

# Include the dashboard router
app.include_router(dashboard_router)

# Mount static files for generated images
assets_path = os.path.join(os.path.dirname(__file__), "..", "assets")
if not os.path.exists(assets_path):
    logger.error(f"❌ Assets path does not exist: {assets_path}")
else:
    logger.info(f"✅ Assets path exists: {assets_path}")
    img_path = os.path.join(assets_path, "generated_images")
    if os.path.exists(img_path):
        images = os.listdir(img_path)
        logger.info(f"📸 Found {len(images)} images in {img_path}")
    
app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
logger.info(f"📁 Serving static files from: {assets_path}")

logger.info("🚀 TwinSpark Chronicles API Starting...")
logger.info(f"Environment: {settings.APP_ENV}")
logger.info(f"Debug Mode: {settings.DEBUG}")
logger.info(f"Host: {settings.HOST}")
logger.info(f"Port: {settings.PORT}")
logger.info(f"Google API: {'✓ Configured' if settings.GOOGLE_API_KEY else '✗ Missing'}")
logger.info(f"HuggingFace API: {'✓ Configured' if settings.HUGGINGFACE_API_KEY else '✗ Missing'}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
