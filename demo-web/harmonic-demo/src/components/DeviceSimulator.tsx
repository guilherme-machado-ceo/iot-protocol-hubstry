'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Thermometer, Droplets, Lightbulb, Shield, Wifi, Radio, Bluetooth, Zap } from 'lucide-react';

interface Device {
  id: string;
  name: string;
  type: 'sensor' | 'actuator' | 'security';
  channel: number;
  frequency: number;
  status: 'active' | 'idle' | 'transmitting';
  value?: string;
  icon: React.ReactNode;
  color: string;
  interface: 'LoRa' | 'BLE' | 'Wi-Fi';
}

interface DeviceSimulatorProps {
  fundamentalFreq: number;
  onChannelActivity: (channels: number[]) => void;
  isSimulating: boolean;
}

export default function DeviceSimulator({ fundamentalFreq, onChannelActivity, isSimulating }: DeviceSimulatorProps) {
  const [devices, setDevices] = useState<Device[]>([
    {
      id: 'temp-sensor-01',
      name: 'Temperature Sensor',
      type: 'sensor',
      channel: 3,
      frequency: 3000,
      status: 'idle',
      value: '23.5°C',
      icon: <Thermometer className="w-5 h-5" />,
      color: 'text-green-400',
      interface: 'LoRa'
    },
    {
      id: 'humidity-sensor-01',
      name: 'Humidity Sensor',
      type: 'sensor',
      channel: 4,
      frequency: 4000,
      status: 'idle',
      value: '65%',
      icon: <Droplets className="w-5 h-5" />,
      color: 'text-green-400',
      interface: 'LoRa'
    },
    {
      id: 'led-actuator-01',
      name: 'LED Controller',
      type: 'actuator',
      channel: 5,
      frequency: 5000,
      status: 'idle',
      value: 'OFF',
      icon: <Lightbulb className="w-5 h-5" />,
      color: 'text-green-400',
      interface: 'LoRa'
    },
    {
      id: 'security-monitor-01',
      name: 'Security Monitor',
      type: 'security',
      channel: 7,
      frequency: 7000,
      status: 'idle',
      value: 'SECURE',
      icon: <Shield className="w-5 h-5" />,
      color: 'text-purple-400',
      interface: 'BLE'
    },
    {
      id: 'wifi-gateway-01',
      name: 'Wi-Fi Gateway',
      type: 'sensor',
      channel: 10,
      frequency: 10000,
      status: 'idle',
      value: 'ONLINE',
      icon: <Wifi className="w-5 h-5" />,
      color: 'text-blue-400',
      interface: 'Wi-Fi'
    }
  ]);

  const [transmissionLog, setTransmissionLog] = useState<string[]>([]);

  useEffect(() => {
    // Update frequencies when fundamental changes
    setDevices(prev => prev.map(device => ({
      ...device,
      frequency: fundamentalFreq * device.channel
    })));
  }, [fundamentalFreq]);

  useEffect(() => {
    if (isSimulating) {
      const interval = setInterval(() => {
        setDevices(prev => {
          const updated = prev.map(device => {
            const shouldTransmit = Math.random() > 0.6;
            
            if (shouldTransmit) {
              let newValue = device.value;
              
              // Simulate realistic data changes
              switch (device.type) {
                case 'sensor':
                  if (device.name.includes('Temperature')) {
                    newValue = `${(20 + Math.random() * 15).toFixed(1)}°C`;
                  } else if (device.name.includes('Humidity')) {
                    newValue = `${(40 + Math.random() * 40).toFixed(0)}%`;
                  } else if (device.name.includes('Wi-Fi')) {
                    newValue = Math.random() > 0.9 ? 'OFFLINE' : 'ONLINE';
                  }
                  break;
                case 'actuator':
                  newValue = Math.random() > 0.5 ? 'ON' : 'OFF';
                  break;
                case 'security':
                  newValue = Math.random() > 0.95 ? 'ALERT' : 'SECURE';
                  break;
              }

              return {
                ...device,
                status: 'transmitting' as const,
                value: newValue
              };
            }
            
            return { ...device, status: 'active' as const };
          });

          // Extract active channels for visualization
          const activeChannels = updated
            .filter(device => device.status === 'transmitting')
            .map(device => device.channel);
          
          onChannelActivity(activeChannels);

          // Add to transmission log
          updated.forEach(device => {
            if (device.status === 'transmitting') {
              setTransmissionLog(prev => {
                const newLog = `[${new Date().toLocaleTimeString()}] H${device.channel} (${device.frequency}Hz): ${device.name} → ${device.value}`;
                return [newLog, ...prev.slice(0, 9)]; // Keep last 10 entries
              });
            }
          });

          return updated;
        });
      }, 2000);

      return () => clearInterval(interval);
    } else {
      setDevices(prev => prev.map(device => ({ ...device, status: 'idle' as const })));
      onChannelActivity([]);
    }
  }, [isSimulating, onChannelActivity, fundamentalFreq]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'transmitting': return 'bg-yellow-500';
      case 'active': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  const getInterfaceIcon = (interfaceType: string) => {
    switch (interfaceType) {
      case 'LoRa': return <Radio className="w-4 h-4" />;
      case 'BLE': return <Bluetooth className="w-4 h-4" />;
      case 'Wi-Fi': return <Wifi className="w-4 h-4" />;
      default: return <Zap className="w-4 h-4" />;
    }
  };

  return (
    <div className="bg-black/30 backdrop-blur-sm rounded-xl border border-purple-500/20 p-6">
      <h3 className="text-lg font-bold text-white mb-4">IoT Device Network</h3>
      
      {/* Device Grid */}
      <div className="grid grid-cols-1 gap-4 mb-6">
        {devices.map((device, index) => (
          <motion.div
            key={device.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`p-4 rounded-lg border transition-all ${
              device.status === 'transmitting' 
                ? 'bg-yellow-500/10 border-yellow-500/30 shadow-lg shadow-yellow-500/20' 
                : device.status === 'active'
                ? 'bg-green-500/10 border-green-500/30'
                : 'bg-gray-500/10 border-gray-500/30'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className={`${device.color}`}>
                  {device.icon}
                </div>
                <div>
                  <p className="text-white font-medium text-sm">{device.name}</p>
                  <div className="flex items-center space-x-2 text-xs text-gray-300">
                    {getInterfaceIcon(device.interface)}
                    <span>H{device.channel} ({device.frequency.toLocaleString()}Hz)</span>
                  </div>
                </div>
              </div>
              
              <div className="text-right">
                <div className="flex items-center space-x-2 mb-1">
                  <div className={`w-2 h-2 rounded-full ${getStatusColor(device.status)} animate-pulse`}></div>
                  <span className="text-white font-mono text-sm">{device.value}</span>
                </div>
                <span className={`text-xs px-2 py-1 rounded ${
                  device.status === 'transmitting' ? 'bg-yellow-500/20 text-yellow-300' :
                  device.status === 'active' ? 'bg-green-500/20 text-green-300' :
                  'bg-gray-500/20 text-gray-300'
                }`}>
                  {device.status.toUpperCase()}
                </span>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Transmission Log */}
      <div className="bg-black/50 rounded-lg p-4 border border-purple-500/10">
        <h4 className="text-white font-medium mb-2 flex items-center space-x-2">
          <Zap className="w-4 h-4 text-yellow-400" />
          <span>Live Transmission Log</span>
        </h4>
        <div className="max-h-32 overflow-y-auto space-y-1">
          {transmissionLog.length > 0 ? (
            transmissionLog.map((log, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="text-xs font-mono text-gray-300 bg-black/30 p-2 rounded border-l-2 border-purple-500/50"
              >
                {log}
              </motion.div>
            ))
          ) : (
            <p className="text-gray-500 text-xs italic">No transmissions yet...</p>
          )}
        </div>
      </div>
    </div>
  );
}
