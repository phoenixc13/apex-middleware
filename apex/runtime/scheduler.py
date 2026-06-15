"""
APEX Scheduler - RT-aware task scheduler
Minimal stub for MVP
"""
import asyncio
import logging

logger = logging.getLogger("apex.scheduler")


class ApexScheduler:
    def __init__(self):
        self._running = False

    async def start(self):
        self._running = True
        logger.info("[Scheduler] APEX Scheduler started")

    async def stop(self):
        self._running = False
        logger.info("[Scheduler] APEX Scheduler stopped")
