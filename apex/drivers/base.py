"""Base Robot Driver Interface for APEX"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio


class RobotDriver(ABC):
    """Abstract base class for all robot drivers"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.connected = False
        self._running = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to robot hardware"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from robot hardware"""
        pass
    
    @abstractmethod
    async def send_command(self, command: Dict[str, Any]) -> bool:
        """Send command to robot"""
        pass
    
    @abstractmethod
    async def get_state(self) -> Dict[str, Any]:
        """Get current robot state"""
        pass
    
    @abstractmethod
    async def emergency_stop(self) -> bool:
        """Emergency stop robot"""
        pass
    
    async def start(self):
        """Start driver"""
        if await self.connect():
            self._running = True
            self.connected = True
            return True
        return False
    
    async def stop(self):
        """Stop driver"""
        self._running = False
        await self.disconnect()
        self.connected = False


class SerialRobotDriver(RobotDriver):
    """Base class for serial-based robots (Arduino, etc.)"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.port = config.get('port', '/dev/ttyUSB0')
        self.baudrate = config.get('baudrate', 115200)
        self.serial = None
    
    async def connect(self) -> bool:
        """Connect to serial port"""
        try:
            import serial
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            return True
        except Exception as e:
            print(f"Failed to connect to {self.port}: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from serial port"""
        if self.serial:
            self.serial.close()
        return True


class NetworkRobotDriver(RobotDriver):
    """Base class for network-based robots (TCP/IP, UDP)"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 5000)
        self.reader = None
        self.writer = None
    
    async def connect(self) -> bool:
        """Connect via TCP/IP"""
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port
            )
            return True
        except Exception as e:
            print(f"Failed to connect to {self.host}:{self.port}: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from network"""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        return True
