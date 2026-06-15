"""
APEX API Routes - REST + WebSocket endpoints
Full API for dashboard, CLI, and external integrations
"""
import asyncio
import time
from typing import Any, Optional, Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Body
from pydantic import BaseModel
import psutil
import logging

from apex.runtime.broker import ApexBroker, QoSPolicy
from apex.runtime.registry import NodeRegistry
from apex.runtime.scheduler import ApexScheduler
from apex.ai.router import AIRouter, AIRequest
from apex.main import broker, registry, scheduler, ai_router

logger = logging.getLogger("apex.api")
router = APIRouter()


# ──────────────────────────────────────────────
# MODELS
# ──────────────────────────────────────────────

class PublishRequest(BaseModel):
    topic: str
    data: Any
    publisher_id: str = "api"
    qos: str = "best_effort"


class SubscribeRequest(BaseModel):
    topic: str
    node_id: str = "api_subscriber"


class AICallRequest(BaseModel):
    role: str = "runtime_ai"
    prompt: str
    system_prompt: Optional[str] = None
    max_tokens: int = 1024


class AddProviderRequest(BaseModel):
    role: str
    name: str
    model: str
    api_key: str
    endpoint: Optional[str] = None
    max_tokens: int = 2048
    temperature: float = 0.3


class RobotCommandRequest(BaseModel):
    command: str
    params: Optional[Dict[str, Any]] = None
    target: str = "default"


# ──────────────────────────────────────────────
# SYSTEM
# ──────────────────────────────────────────────

@router.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "0.1.0",
        "uptime": time.time(),
        "broker": broker.stats()
    }


@router.get("/status")
async def status():
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    return {
        "apex": {
            "version": "0.1.0",
            "status": "running"
        },
        "broker": broker.stats(),
        "nodes": registry.list_nodes(),
        "ai_providers": ai_router.get_providers(),
        "system": {
            "cpu_percent": cpu,
            "memory_percent": mem.percent,
            "memory_used_gb": round(mem.used / 1e9, 2),
            "memory_total_gb": round(mem.total / 1e9, 2)
        }
    }


# ──────────────────────────────────────────────
# TOPICS
# ──────────────────────────────────────────────

@router.get("/topics")
async def list_topics():
    topics = broker.get_topics()
    result = []
    for name, info in topics.items():
        latency = broker.get_topic_latency(name)
        result.append({
            "name": name,
            "message_count": info.message_count,
            "subscriber_count": info.subscriber_count,
            "publisher_count": info.publisher_count,
            "hz": round(info.hz, 2),
            "last_message_at": info.last_message_at,
            "latency_us": latency
        })
    return {"topics": result, "count": len(result)}


@router.post("/topics/publish")
async def publish(req: PublishRequest):
    qos = QoSPolicy(req.qos) if req.qos in QoSPolicy.__members__.values() else QoSPolicy.BEST_EFFORT
    delivered = await broker.publish(
        topic=req.topic,
        data=req.data,
        publisher_id=req.publisher_id,
        qos=qos
    )
    return {
        "published": True,
        "topic": req.topic,
        "delivered_to": delivered
    }


@router.get("/topics/{topic}/latency")
async def topic_latency(topic: str):
    return {"topic": topic, "latency_us": broker.get_topic_latency(topic)}


# ──────────────────────────────────────────────
# NODES
# ──────────────────────────────────────────────

@router.get("/nodes")
async def list_nodes():
    return {"nodes": registry.list_nodes()}


@router.post("/nodes/register")
async def register_node(name: str, node_type: str = "generic"):
    node_id = registry.register(name=name, node_type=node_type)
    return {"node_id": node_id, "name": name}


# ──────────────────────────────────────────────
# AI
# ──────────────────────────────────────────────

@router.get("/ai/providers")
async def list_providers():
    return {"providers": ai_router.get_providers()}


@router.post("/ai/providers")
async def add_provider(req: AddProviderRequest):
    ai_router.add_provider(
        role=req.role,
        name=req.name,
        model=req.model,
        api_key=req.api_key,
        endpoint=req.endpoint,
        max_tokens=req.max_tokens,
        temperature=req.temperature
    )
    return {"added": True, "role": req.role, "name": req.name, "model": req.model}


@router.post("/ai/call")
async def ai_call(req: AICallRequest):
    ai_req = AIRequest(
        role=req.role,
        prompt=req.prompt,
        system_prompt=req.system_prompt,
        max_tokens=req.max_tokens
    )
    resp = await ai_router.call(ai_req)
    return {
        "content": resp.content,
        "provider": resp.provider,
        "model": resp.model,
        "latency_ms": resp.latency_ms,
        "success": resp.success,
        "error": resp.error
    }


@router.get("/ai/history")
async def ai_history(limit: int = 50):
    return {"history": ai_router.history(limit)}


# ──────────────────────────────────────────────
# ROBOT
# ──────────────────────────────────────────────

@router.post("/robot/command")
async def robot_command(req: RobotCommandRequest):
    """Send a command to the robot via AI-assisted planning."""
    # Build prompt for robot AI
    prompt = f"""Robot command request:
Command: {req.command}
Params: {req.params}
Target: {req.target}

Generate a structured robot action plan. Return JSON with: action, params, safety_check, estimated_duration_ms."""

    ai_req = AIRequest(
        role="robot_ai",
        prompt=prompt,
        system_prompt="You are an advanced robot command interpreter. Always prioritize safety. Return valid JSON.",
        max_tokens=512
    )
    resp = await ai_router.call(ai_req)

    # Also publish to APEX topic for any node subscribers
    await broker.publish(
        topic="/robot/commands",
        data={"command": req.command, "params": req.params, "ai_response": resp.content},
        publisher_id="api"
    )

    return {
        "command": req.command,
        "ai_plan": resp.content,
        "provider": resp.provider,
        "latency_ms": resp.latency_ms,
        "published_to": "/robot/commands"
    }


# ──────────────────────────────────────────────
# WEBSOCKET - Live dashboard feed
# ──────────────────────────────────────────────

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    broker.add_ws_client(websocket)
    logger.info("[WS] Dashboard client connected")

    try:
        # Send initial state
        import json
        init_payload = json.dumps({
            "type": "init",
            "version": "0.1.0",
            "broker": broker.stats(),
            "providers": ai_router.get_providers()
        })
        await websocket.send_text(init_payload)

        # Keep alive + send periodic system stats
        while True:
            await asyncio.sleep(2)
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory()
            stats_payload = json.dumps({
                "type": "system_stats",
                "cpu": cpu,
                "memory": mem.percent,
                "topics": len(broker.get_topics()),
                "ts": time.time()
            })
            await websocket.send_text(stats_payload)

    except WebSocketDisconnect:
        broker.remove_ws_client(websocket)
        logger.info("[WS] Dashboard client disconnected")
    except Exception as e:
        broker.remove_ws_client(websocket)
        logger.error(f"[WS] Error: {e}")
