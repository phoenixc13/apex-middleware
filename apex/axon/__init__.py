"""AXON - Binary IDL for APEX Middleware

Internal binary Interface Definition Language for ultra-low latency
message serialization/deserialization.
"""

from .serializer import AxonSerializer, AxonMessage
from .types import AxonType

__version__ = "0.1.0"
__all__ = ["AxonSerializer", "AxonMessage", "AxonType"]
