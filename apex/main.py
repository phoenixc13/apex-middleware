"""
APEX Middleware - Main Entry Point
Ultra-low latency robotic middleware with AI orchestration
"""
import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import logging
import os

from apex.runtime.broker import ApexBroker
from apex.runtime.registry import NodeRegistry
from apex.api.routes import router as api_router
from apex.ai.router import AIRouter
from apex.runtime.scheduler import ApexScheduler

logging.basicConfig(
    level=logging.INFO,
    format="\033[33m[APEX]\033[0m %(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger("apex")

# Global singletons
broker = ApexBroker()
registry = NodeRegistry()
scheduler = ApexScheduler()
ai_router = AIRouter()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("="*60)
    logger.info("  APEX MIDDLEWARE v0.1.0 - STARTING")
    logger.info("  Ultra-Low Latency Robotic Middleware")
    logger.info("  ROS 2 Competitor | AI-Native | Binary IDL")
    logger.info("="*60)

    # Start core subsystems
    await broker.start()
    await scheduler.start()
    await ai_router.load_providers()

    logger.info("[APEX] All subsystems online. Dashboard: http://localhost:8000")
    yield

    # Shutdown
    logger.info("[APEX] Shutting down...")
    await broker.stop()
    await scheduler.stop()


app = FastAPI(
    title="APEX Middleware",
    description="Ultra-low latency robotic middleware with AI orchestration",
    version="0.1.0",
    lifespan=lifespan
)

# API routes
app.include_router(api_router, prefix="/api")

# Serve dashboard
dashboard_path = os.path.join(os.path.dirname(__file__), "..", "dashboard")
if os.path.exists(dashboard_path):
    app.mount("/static", StaticFiles(directory=dashboard_path), name="static")

    @app.get("/")
    async def serve_dashboard():
        return FileResponse(os.path.join(dashboard_path, "index.html"))
else:
    @app.get("/")
    async def root():
        return {
            "name": "APEX Middleware",
            "version": "0.1.0",
            "status": "running",
            "dashboard": "dashboard/ folder not found",
            "docs": "/docs"
        }


if __name__ == "__main__":
    uvicorn.run(
        "apex.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
        ws_ping_interval=20,
        ws_ping_timeout=20,
    )
