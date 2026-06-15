"""AXON Type System - Data type definitions for AXON protocol"""

from enum import Enum
from typing import Union
import struct


class AxonType(Enum):
    """AXON binary data types"""
    
    # Primitive types
    INT8 = 0x01
    INT16 = 0x02
    INT32 = 0x03
    INT64 = 0x04
    UINT8 = 0x05
    UINT16 = 0x06
    UINT32 = 0x07
    UINT64 = 0x08
    
    FLOAT32 = 0x10
    FLOAT64 = 0x11
    
    BOOL = 0x20
    STRING = 0x21
    BYTES = 0x22
    
    # Complex types
    ARRAY = 0x30
    DICT = 0x31
    
    # Robot-specific types
    POSE = 0x40
    TWIST = 0x41
    QUATERNION = 0x42
    TRANSFORM = 0x43
    
    @classmethod
    def get_format(cls, axon_type: 'AxonType') -> str:
        """Get struct format string for type"""
        formats = {
            cls.INT8: 'b',
            cls.INT16: 'h',
            cls.INT32: 'i',
            cls.INT64: 'q',
            cls.UINT8: 'B',
            cls.UINT16: 'H',
            cls.UINT32: 'I',
            cls.UINT64: 'Q',
            cls.FLOAT32: 'f',
            cls.FLOAT64: 'd',
            cls.BOOL: '?',
        }
        return formats.get(axon_type, '')
    
    @classmethod
    def get_size(cls, axon_type: 'AxonType') -> int:
        """Get byte size for type"""
        fmt = cls.get_format(axon_type)
        if fmt:
            return struct.calcsize(fmt)
        return -1  # Variable size


class TypeRegistry:
    """Registry for custom AXON types"""
    
    def __init__(self):
        self._custom_types = {}
    
    def register(self, name: str, type_id: int, schema: dict):
        """Register a custom type"""
        self._custom_types[name] = {
            'id': type_id,
            'schema': schema
        }
    
    def get(self, name: str) -> dict:
        """Get custom type definition"""
        return self._custom_types.get(name)
    
    def list_types(self) -> list:
        """List all registered types"""
        return list(self._custom_types.keys())
