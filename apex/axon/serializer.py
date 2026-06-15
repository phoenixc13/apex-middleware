"""AXON Binary Serializer - Ultra-low latency message serialization"""

import struct
import time
from typing import Any, Dict, Optional
from .types import AxonType


class AxonMessage:
    """Binary message container for AXON protocol"""
    
    def __init__(self, msg_type: str, payload: Dict[str, Any], priority: int = 0):
        self.msg_type = msg_type
        self.payload = payload
        self.priority = priority
        self.timestamp = time.time_ns()
        self.msg_id = id(self)
    
    def __repr__(self):
        return f"AxonMessage(type={self.msg_type}, priority={self.priority})"


class AxonSerializer:
    """Binary serializer for ultra-low latency message passing"""
    
    HEADER_FORMAT = "!IQHH"  # Magic(4), Timestamp(8), Priority(2), Type_len(2)
    MAGIC = 0x41584F4E  # 'AXON' in hex
    
    def __init__(self):
        self.header_size = struct.calcsize(self.HEADER_FORMAT)
    
    def serialize(self, message: AxonMessage) -> bytes:
        """Serialize AxonMessage to binary format"""
        type_bytes = message.msg_type.encode('utf-8')
        payload_bytes = self._encode_payload(message.payload)
        
        # Pack header: magic, timestamp, priority, type_length
        header = struct.pack(
            self.HEADER_FORMAT,
            self.MAGIC,
            message.timestamp,
            message.priority,
            len(type_bytes)
        )
        
        return header + type_bytes + payload_bytes
    
    def deserialize(self, data: bytes) -> Optional[AxonMessage]:
        """Deserialize binary data to AxonMessage"""
        if len(data) < self.header_size:
            return None
        
        # Unpack header
        magic, timestamp, priority, type_len = struct.unpack(
            self.HEADER_FORMAT,
            data[:self.header_size]
        )
        
        if magic != self.MAGIC:
            raise ValueError("Invalid AXON message magic")
        
        # Extract message type
        offset = self.header_size
        msg_type = data[offset:offset + type_len].decode('utf-8')
        offset += type_len
        
        # Decode payload
        payload = self._decode_payload(data[offset:])
        
        msg = AxonMessage(msg_type, payload, priority)
        msg.timestamp = timestamp
        return msg
    
    def _encode_payload(self, payload: Dict[str, Any]) -> bytes:
        """Encode payload to binary (simplified for MVP)"""
        import json
        return json.dumps(payload).encode('utf-8')
    
    def _decode_payload(self, data: bytes) -> Dict[str, Any]:
        """Decode binary payload (simplified for MVP)"""
        import json
        return json.loads(data.decode('utf-8'))
