"""
Harmonic IoT Protocol SDK for Raspberry Pi
==========================================

Official Python SDK for integrating Raspberry Pi devices with the Harmonic IoT Protocol.

Copyright (c) 2025 Guilherme Gonçalves Machado
Licensed under CC BY-NC-SA 4.0

Example usage:
    from harmonic_iot import HarmonicDevice, SensorManager

    device = HarmonicDevice(fundamental_freq=1000)
    device.add_sensor('temperature', 'DS18B20', harmonic_channel=2)
    device.start_communication()
"""

__version__ = "1.0.0"
__author__ = "Guilherme Gonçalves Machado"
__email__ = "guilherme.ceo@hubstry.com"
__license__ = "CC BY-NC-SA 4.0"

from .device import HarmonicDevice
from .sensors import SensorManager, TemperatureSensor, HumiditySensor, PressureSensor
from .communication import HarmonicProtocol, ChannelManager
from .utils import FFTProcessor, FrequencyAnalyzer

__all__ = [
    'HarmonicDevice',
    'SensorManager',
    'TemperatureSensor',
    'HumiditySensor',
    'PressureSensor',
    'HarmonicProtocol',
    'ChannelManager',
    'FFTProcessor',
    'FrequencyAnalyzer'
]
