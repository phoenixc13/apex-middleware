"""
APEX Broker - Core Pub/Sub engine
High-performance async message broker with QoS support
"""
import asyncio
import time
import uuid
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger("apex.broker")


class QoSPolicy(str, Enum):
    BEST_EFFORT = "best_effort"
    RELIABLE = "reliable"
    KEEP_LAST = "keep_last"


class NodeState(str, Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class TopicMessage:
    topic: str
    data: Any
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())
    publisher_id: str = ""
    sequence: int = 0
    qos: QoSPolicy = QoSPolicy.BEST_EFFORT


@dataclass
class Subscription:
    sub_id: str
    topic: str
    callback: Callable
    node_id: str
    qos: QoSPolicy = QoSPolicy.BEST_EFFORT
    created_at: float = field(default_factory=time.time)


@dataclass
class TopicInfo:
    name: str
    message_count: int = 0
    subscriber_count: int = 0
    publisher_count: int = 0
    last_message_at: Optional[float] = None
    hz: float = 0.0
    _last_hz_check: float = field(default_factory=time.time)
    _hz_count: int = 0


class ApexBroker:
    """
    APEX Core Pub/Sub Broker
    - Async publish/subscribe
    - Per-topic QoS
    - Latency tracking
    - WebSocket fan-out for dashboard
    """

    def __init__(self):
        # topic -> list of subscriptions
        self._subscriptions: Dict[str, List[Subscription]] = {}
        # topic -> TopicInfo
        self._topics: Dict[str, TopicInfo] = {}
        # latency tracking
        self._latencies: Dict[str, List[float]] = {}
        # WebSocket clients for dashboard
        self._ws_clients: List[Any] = []
        # message sequence counter per topic
        self._sequences: Dict[str, int] = {}
        self._running = False
        self._lock = asyncio.Lock()

    async def start(self):
        self._running = True
        logger.info("[Broker] APEX Broker started")

    async def stop(self):
        self._running = False
        logger.info("[Broker] APEX Broker stopped")

    async def publish(self, topic: str, data: Any, publisher_id: str = "",
                      qos: QoSPolicy = QoSPolicy.BEST_EFFORT) -> int:
        """Publish a message to a topic. Returns subscriber count reached."""
        t_start = time.time_ns()

        # Ensure topic exists
        if topic not in self._topics:
            self._topics[topic] = TopicInfo(name=topic)
            self._subscriptions[topic] = []
            self._sequences[topic] = 0

        # Build message
        seq = self._sequences[topic]
        self._sequences[topic] += 1
        msg = TopicMessage(
            topic=topic,
            data=data,
            publisher_id=publisher_id,
            sequence=seq,
            qos=qos
        )

        # Update topic stats
        info = self._topics[topic]
        info.message_count += 1
        info.last_message_at = time.time()
        info.publisher_count = max(info.publisher_count, 1)

        # Hz calculation
        info._hz_count += 1
        now = time.time()
        elapsed = now - info._last_hz_check
        if elapsed >= 1.0:
            info.hz = info._hz_count / elapsed
            info._hz_count = 0
            info._last_hz_check = now

        # Deliver to subscribers
        subs = self._subscriptions.get(topic, [])
        delivered = 0
        tasks = []
        for sub in subs:
            tasks.append(self._deliver(sub, msg))
            delivered += 1

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # Track latency
        latency_us = (time.time_ns() - t_start) / 1000
        if topic not in self._latencies:
            self._latencies[topic] = []
        self._latencies[topic].append(latency_us)
        if len(self._latencies[topic]) > 1000:
            self._latencies[topic] = self._latencies[topic][-1000:]

        # Fan-out to WebSocket dashboard clients
        if self._ws_clients:
            asyncio.create_task(self._ws_fanout(topic, data, latency_us))

        return delivered

    async def _deliver(self, sub: Subscription, msg: TopicMessage):
        try:
            if asyncio.iscoroutinefunction(sub.callback):
                await sub.callback(msg)
            else:
                sub.callback(msg)
        except Exception as e:
            logger.error(f"[Broker] Delivery error on {sub.topic}: {e}")

    async def _ws_fanout(self, topic: str, data: Any, latency_us: float):
        import json
        payload = json.dumps({
            "type": "topic_message",
            "topic": topic,
            "data": str(data)[:256],
            "latency_us": round(latency_us, 2),
            "ts": time.time()
        })
        dead = []
        for ws in self._ws_clients:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._ws_clients.remove(ws)

    def subscribe(self, topic: str, callback: Callable, node_id: str = "",
                  qos: QoSPolicy = QoSPolicy.BEST_EFFORT) -> str:
        """Subscribe to a topic. Returns subscription ID."""
        if topic not in self._subscriptions:
            self._subscriptions[topic] = []
            self._topics[topic] = TopicInfo(name=topic)
            self._sequences[topic] = 0

        sub_id = str(uuid.uuid4())[:8]
        sub = Subscription(
            sub_id=sub_id,
            topic=topic,
            callback=callback,
            node_id=node_id,
            qos=qos
        )
        self._subscriptions[topic].append(sub)
        self._topics[topic].subscriber_count += 1
        logger.info(f"[Broker] Node '{node_id}' subscribed to '{topic}' [{sub_id}]")
        return sub_id

    def unsubscribe(self, topic: str, sub_id: str) -> bool:
        subs = self._subscriptions.get(topic, [])
        for sub in subs:
            if sub.sub_id == sub_id:
                subs.remove(sub)
                if topic in self._topics:
                    self._topics[topic].subscriber_count = max(0, self._topics[topic].subscriber_count - 1)
                return True
        return False

    def get_topics(self) -> Dict[str, TopicInfo]:
        return self._topics

    def get_topic_latency(self, topic: str) -> Dict[str, float]:
        lats = self._latencies.get(topic, [])
        if not lats:
            return {"p50": 0, "p95": 0, "p99": 0, "mean": 0}
        sorted_lats = sorted(lats)
        n = len(sorted_lats)
        return {
            "p50": sorted_lats[int(n * 0.50)],
            "p95": sorted_lats[int(n * 0.95)],
            "p99": sorted_lats[int(n * 0.99)],
            "mean": sum(sorted_lats) / n
        }

    def add_ws_client(self, ws):
        self._ws_clients.append(ws)

    def remove_ws_client(self, ws):
        if ws in self._ws_clients:
            self._ws_clients.remove(ws)

    def stats(self) -> dict:
        return {
            "topics": len(self._topics),
            "total_subscriptions": sum(len(v) for v in self._subscriptions.values()),
            "ws_clients": len(self._ws_clients),
            "running": self._running
        }
