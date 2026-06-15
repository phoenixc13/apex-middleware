"""
APEX Node Registry
Tracks active nodes, their state, subscriptions and services
"""
import time
import uuid
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger("apex.registry")


@dataclass
class Node:
    node_id: str
    name: str
    node_type: str = "generic"
    state: str = "active"
    created_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    subscriptions: List[str] = field(default_factory=list)
    publishers: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class NodeRegistry:
    """
    APEX Node Registry
    - Register/unregister nodes
    - Track node lifecycle and health
    - Query nodes by type, state, etc.
    """

    def __init__(self):
        self._nodes: Dict[str, Node] = {}

    def register(self, name: str, node_type: str = "generic", metadata: Optional[Dict] = None) -> str:
        node_id = str(uuid.uuid4())[:12]
        node = Node(
            node_id=node_id,
            name=name,
            node_type=node_type,
            metadata=metadata or {}
        )
        self._nodes[node_id] = node
        logger.info(f"[Registry] Registered node '{name}' [{node_id}]")
        return node_id

    def unregister(self, node_id: str) -> bool:
        if node_id in self._nodes:
            name = self._nodes[node_id].name
            del self._nodes[node_id]
            logger.info(f"[Registry] Unregistered node '{name}' [{node_id}]")
            return True
        return False

    def heartbeat(self, node_id: str):
        if node_id in self._nodes:
            self._nodes[node_id].last_heartbeat = time.time()

    def get_node(self, node_id: str) -> Optional[Node]:
        return self._nodes.get(node_id)

    def list_nodes(self) -> List[Dict]:
        return [
            {
                "node_id": n.node_id,
                "name": n.name,
                "type": n.node_type,
                "state": n.state,
                "uptime": round(time.time() - n.created_at, 1)
            }
            for n in self._nodes.values()
        ]

    def count(self) -> int:
        return len(self._nodes)
