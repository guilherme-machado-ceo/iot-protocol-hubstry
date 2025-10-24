"""
Harmonic IoT Device Implementation for Raspberry Pi
==================================================

Main device class for Raspberry Pi integration with Harmonic IoT Protocol.
"""

import time
import json
import logging
from typing import Dict, List, Optional, Callable
from .communication import HarmonicProtocol, ChannelManager
from .sensors import SensorManager
from .utils import FFTProcessor

logger = logging.getLogger(__name__)

class HarmonicDevice:
    """
    Main Harmonic IoT Device class for Raspberry Pi.

    This class provides the primary interface for integrating Raspberry Pi
    devices with the Harmonic IoT Protocol, including sensor management,
    harmonic communication, and automatic device registration.
    """

    def __init__(self,
                 fundamental_freq: float = 1000.0,
                 device_id: Optional[str] = None,
                 server_url: str = "https://api.harmonic-iot.com",
                 auto_register: bool = True):
        """
        Initialize Harmonic IoT Device.

        Args:
            fundamental_freq: Base frequency for harmonic calculations (Hz)
            device_id: Unique device identifier (auto-generated if None)
            server_url: Harmonic IoT server URL
            auto_register: Automatically register device on startup
        """
        self.fundamental_freq = fundamental_freq
        self.device_id = device_id or self._generate_device_id()
        self.server_url = server_url
        self.auto_register = auto_register

        # Initialize components
        self.protocol = HarmonicProtocol(fundamental_freq, server_url)
        self.channel_manager = ChannelManager()
        self.sensor_manager = SensorManager()
        self.fft_processor = FFTProcessor()

        # Device state
        self.is_connected = False
        self.is_running = False
        self.sensors: Dict[str, any] = {}
        self.harmonic_channels: Dict[int, str] = {}

        logger.info(f"Harmonic device initialized: {self.device_id}")

    def _generate_device_id(self) -> str:
        """Generate unique device ID based on Raspberry Pi serial."""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('Serial'):
                        serial = line.split(':')[1].strip()
                        return f"rpi_{serial}"
        except Exception:
            pass

        # Fallback to timestamp-based ID
        import uuid
        return f"rpi_{str(uuid.uuid4())[:8]}"

    def add_sensor(self,
                   sensor_name: str,
                   sensor_type: str,
                   harmonic_channel: int,
                   gpio_pin: Optional[int] = None,
                   i2c_address: Optional[int] = None,
                   **kwargs) -> bool:
        """
        Add sensor to the device.

        Args:
            sensor_name: Human-readable sensor name
            sensor_type: Sensor type (DS18B20, DHT22, BMP280, etc.)
            harmonic_channel: Harmonic channel for this sensor
            gpio_pin: GPIO pin number (if applicable)
            i2c_address: I2C address (if applicable)
            **kwargs: Additional sensor-specific parameters

        Returns:
            bool: True if sensor added successfully
        """
        try:
            sensor = self.sensor_manager.create_sensor(
                sensor_type,
                gpio_pin=gpio_pin,
                i2c_address=i2c_address,
                **kwargs
            )

            if sensor:
                self.sensors[sensor_name] = sensor
                self.harmonic_channels[harmonic_channel] = sensor_name
                self.channel_manager.assign_channel(harmonic_channel, sensor_name)

                logger.info(f"Added sensor {sensor_name} ({sensor_type}) on channel H{harmonic_channel}")
                return True

        except Exception as e:
            logger.error(f"Failed to add sensor {sensor_name}: {e}")

        return False

    def connect(self) -> bool:
        """
        Connect to Harmonic IoT network.

        Returns:
            bool: True if connected successfully
        """
        try:
            # Connect to server
            if self.protocol.connect():
                self.is_connected = True

                # Auto-register device if enabled
                if self.auto_register:
                    self.register_device()

                # Synchronize fundamental frequency
                self.synchronize_frequency()

                logger.info("Connected to Harmonic IoT network")
                return True

        except Exception as e:
            logger.error(f"Connection failed: {e}")

        return False

    def register_device(self) -> bool:
        """
        Register device with Harmonic IoT server.

        Returns:
            bool: True if registration successful
        """
        try:
            device_info = {
                "device_id": self.device_id,
                "device_type": "raspberry_pi",
                "fundamental_freq": self.fundamental_freq,
                "sensors": list(self.sensors.keys()),
                "harmonic_channels": self.harmonic_channels,
                "capabilities": self._get_device_capabilities()
            }

            if self.protocol.register_device(device_info):
                logger.info("Device registered successfully")
                return True

        except Exception as e:
            logger.error(f"Device registration failed: {e}")

        return False

    def synchronize_frequency(self) -> bool:
        """
        Synchronize fundamental frequency with network.

        Returns:
            bool: True if synchronization successful
        """
        try:
            network_freq = self.protocol.get_network_frequency()
            if network_freq and network_freq != self.fundamental_freq:
                self.fundamental_freq = network_freq
                self.fft_processor.update_fundamental_freq(network_freq)
                logger.info(f"Synchronized to network frequency: {network_freq} Hz")

            return True

        except Exception as e:
            logger.error(f"Frequency synchronization failed: {e}")
            return False

    def start_communication(self,
                          sampling_interval: float = 1.0,
                          callback: Optional[Callable] = None) -> None:
        """
        Start harmonic communication loop.

        Args:
            sampling_interval: Sensor sampling interval in seconds
            callback: Optional callback function for custom processing
        """
        if not self.is_connected:
            if not self.connect():
                raise RuntimeError("Failed to connect to network")

        self.is_running = True
        logger.info("Starting harmonic communication")

        try:
            while self.is_running:
                # Read all sensors
                sensor_data = self._read_all_sensors()

                # Process and transmit data for each harmonic channel
                for channel, sensor_name in self.harmonic_channels.items():
                    if sensor_name in sensor_data:
                        data = sensor_data[sensor_name]

                        # Apply harmonic modulation
                        harmonic_data = self._modulate_harmonic_data(channel, data)

                        # Transmit on harmonic channel
                        self.protocol.transmit_harmonic_data(channel, harmonic_data)

                        logger.debug(f"Transmitted data on H{channel}: {data}")

                # Custom callback processing
                if callback:
                    callback(sensor_data)

                # Wait for next sampling interval
                time.sleep(sampling_interval)

        except KeyboardInterrupt:
            logger.info("Communication stopped by user")
        except Exception as e:
            logger.error(f"Communication error: {e}")
        finally:
            self.stop_communication()

    def stop_communication(self) -> None:
        """Stop harmonic communication."""
        self.is_running = False
        if self.is_connected:
            self.protocol.disconnect()
            self.is_connected = False
        logger.info("Harmonic communication stopped")

    def _read_all_sensors(self) -> Dict[str, any]:
        """Read data from all configured sensors."""
        sensor_data = {}

        for sensor_name, sensor in self.sensors.items():
            try:
                data = sensor.read()
                sensor_data[sensor_name] = data
            except Exception as e:
                logger.warning(f"Failed to read sensor {sensor_name}: {e}")

        return sensor_data

    def _modulate_harmonic_data(self, channel: int, data: any) -> Dict:
        """
        Apply harmonic modulation to sensor data.

        Args:
            channel: Harmonic channel number
            data: Raw sensor data

        Returns:
            Dict: Modulated harmonic data
        """
        harmonic_freq = self.fundamental_freq * channel

        # Create harmonic signature
        harmonic_data = {
            "frequency": harmonic_freq,
            "channel": channel,
            "data": data,
            "timestamp": time.time(),
            "device_id": self.device_id,
            "signature": self._generate_harmonic_signature(channel, data)
        }

        return harmonic_data

    def _generate_harmonic_signature(self, channel: int, data: any) -> str:
        """Generate harmonic signature for authentication."""
        import hashlib

        signature_data = f"{self.device_id}:{channel}:{data}:{self.fundamental_freq}"
        return hashlib.sha256(signature_data.encode()).hexdigest()[:16]

    def _get_device_capabilities(self) -> List[str]:
        """Get list of device capabilities."""
        capabilities = ["harmonic_communication", "sensor_reading", "fft_processing"]

        # Add sensor-specific capabilities
        for sensor in self.sensors.values():
            capabilities.extend(sensor.get_capabilities())

        return list(set(capabilities))

    def get_status(self) -> Dict:
        """
        Get current device status.

        Returns:
            Dict: Device status information
        """
        return {
            "device_id": self.device_id,
            "is_connected": self.is_connected,
            "is_running": self.is_running,
            "fundamental_freq": self.fundamental_freq,
            "sensor_count": len(self.sensors),
            "active_channels": list(self.harmonic_channels.keys()),
            "uptime": time.time() - getattr(self, '_start_time', time.time())
        }

    def __enter__(self):
        """Context manager entry."""
        self._start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_communication()
