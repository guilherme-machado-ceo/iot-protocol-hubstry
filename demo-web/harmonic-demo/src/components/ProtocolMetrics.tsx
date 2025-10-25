'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, Cpu, Network, Shield, Clock, Zap, Key } from 'lucide-react';

interface ProtocolMetricsProps {
  activeChannels: number[];
  isSimulating: boolean;
}

interface Metrics {
  throughput: number;
  latency: number;
  channelUtilization: number;
  securityEvents: number;
  packetsProcessed: number;
  errorRate: number;
  invalidSignatureRate: number;
  kyberKeyUsage: number;
}

export default function ProtocolMetrics({ activeChannels, isSimulating }: ProtocolMetricsProps) {
  const [metrics, setMetrics] = useState<Metrics>({
    throughput: 0,
    latency: 0,
    channelUtilization: 0,
    securityEvents: 0,
    packetsProcessed: 0,
    errorRate: 0,
    invalidSignatureRate: 0,
    kyberKeyUsage: 0
  });

  const [historicalData, setHistoricalData] = useState<number[]>([]);

  useEffect(() => {
    if (isSimulating) {
      const interval = setInterval(() => {
        setMetrics(prev => {
          const newThroughput = activeChannels.length * (50 + Math.random() * 100);
          const newLatency = 15 + Math.random() * 20;
          const newUtilization = (activeChannels.length / 16) * 100;
          const newPackets = prev.packetsProcessed + activeChannels.length * (1 + Math.floor(Math.random() * 5));
          const newErrorRate = Math.random() * 0.1;
          const newSecurityEvents = prev.securityEvents + (Math.random() > 0.95 ? 1 : 0);
          const newInvalidSignatureRate = Math.random() * 0.05;
          const newKyberKeyUsage = prev.kyberKeyUsage + (activeChannels.length > 0 ? 1 : 0);

          return {
            throughput: newThroughput,
            latency: newLatency,
            channelUtilization: newUtilization,
            securityEvents: newSecurityEvents,
            packetsProcessed: newPackets,
            errorRate: newErrorRate,
            invalidSignatureRate: newInvalidSignatureRate,
            kyberKeyUsage: newKyberKeyUsage
          };
        });

        setHistoricalData(prev => {
          const newData = [...prev, activeChannels.length * 10];
          return newData.slice(-20); // Keep last 20 data points
        });
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [isSimulating, activeChannels]);

  const MetricCard = ({ 
    title, 
    value, 
    unit, 
    icon, 
    color, 
    trend 
  }: { 
    title: string; 
    value: number | string; 
    unit: string; 
    icon: React.ReactNode; 
    color: string;
    trend?: 'up' | 'down' | 'stable';
  }) => (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="bg-black/50 rounded-lg p-4 border border-purple-500/10"
    >
      <div className="flex items-center justify-between mb-2">
        <div className={`${color}`}>
          {icon}
        </div>
        {trend && (
          <div className={`flex items-center space-x-1 text-xs ${
            trend === 'up' ? 'text-green-400' : 
            trend === 'down' ? 'text-red-400' : 'text-gray-400'
          }`}>
            <TrendingUp className={`w-3 h-3 ${trend === 'down' ? 'rotate-180' : ''}`} />
          </div>
        )}
      </div>
      <div>
        <p className="text-2xl font-bold text-white">
          {typeof value === 'number' ? value.toFixed(1) : value}
          <span className="text-sm font-normal text-gray-400 ml-1">{unit}</span>
        </p>
        <p className="text-gray-400 text-xs">{title}</p>
      </div>
    </motion.div>
  );

  return (
    <div className="bg-black/30 backdrop-blur-sm rounded-xl border border-purple-500/20 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-white">Protocol Performance Metrics</h3>
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${isSimulating ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}`}></div>
          <span className="text-gray-300 text-sm">
            {isSimulating ? 'Live Monitoring' : 'Simulation Stopped'}
          </span>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        <MetricCard
          title="Throughput"
          value={metrics.throughput}
          unit="Kbps"
          icon={<TrendingUp className="w-5 h-5" />}
          color="text-green-400"
          trend="up"
        />
        <MetricCard
          title="Latency"
          value={metrics.latency}
          unit="ms"
          icon={<Clock className="w-5 h-5" />}
          color="text-blue-400"
          trend="stable"
        />
        <MetricCard
          title="Channel Usage"
          value={metrics.channelUtilization}
          unit="%"
          icon={<Network className="w-5 h-5" />}
          color="text-purple-400"
          trend="up"
        />
        <MetricCard
          title="Security Events"
          value={metrics.securityEvents}
          unit=""
          icon={<Shield className="w-5 h-5" />}
          color="text-red-400"
        />
        <MetricCard
          title="Packets"
          value={metrics.packetsProcessed}
          unit=""
          icon={<Cpu className="w-5 h-5" />}
          color="text-yellow-400"
          trend="up"
        />
        <MetricCard
          title="Error Rate"
          value={metrics.errorRate}
          unit="%"
          icon={<Zap className="w-5 h-5" />}
          color="text-orange-400"
          trend="down"
        />
        <MetricCard
          title="Invalid Signatures"
          value={metrics.invalidSignatureRate}
          unit="%"
          icon={<Shield className="w-5 h-5" />}
          color="text-red-400"
        />
        <MetricCard
          title="Kyber Keys Used"
          value={metrics.kyberKeyUsage}
          unit=""
          icon={<Key className="w-5 h-5" />}
          color="text-teal-400"
        />
      </div>

      {/* Real-time Chart */}
      <div className="bg-black/50 rounded-lg p-4 border border-purple-500/10">
        <h4 className="text-white font-medium mb-4">Channel Activity Over Time</h4>
        <div className="relative h-24">
          <svg className="w-full h-full" viewBox="0 0 400 100">
            {/* Grid lines */}
            {[0, 25, 50, 75, 100].map(y => (
              <line
                key={y}
                x1="0"
                y1={y}
                x2="400"
                y2={y}
                stroke="rgba(147, 51, 234, 0.2)"
                strokeWidth="1"
              />
            ))}
            
            {/* Data line */}
            {historicalData.length > 1 && (
              <polyline
                fill="none"
                stroke="rgba(147, 51, 234, 0.8)"
                strokeWidth="2"
                points={historicalData
                  .map((value, index) => {
                    const x = (index / (historicalData.length - 1)) * 400;
                    const y = 100 - (value / Math.max(...historicalData, 1)) * 80;
                    return `${x},${y}`;
                  })
                  .join(' ')
                }
              />
            )}
            
            {/* Data points */}
            {historicalData.map((value, index) => {
              const x = (index / Math.max(historicalData.length - 1, 1)) * 400;
              const y = 100 - (value / Math.max(...historicalData, 1)) * 80;
              return (
                <circle
                  key={index}
                  cx={x}
                  cy={y}
                  r="3"
                  fill="rgba(147, 51, 234, 0.8)"
                  className="animate-pulse"
                />
              );
            })}
          </svg>
        </div>
        <div className="flex justify-between text-xs text-gray-400 mt-2">
          <span>-20s</span>
          <span>Channel Activity</span>
          <span>Now</span>
        </div>
      </div>

      {/* Key Benefits */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-gradient-to-r from-green-500/10 to-blue-500/10 rounded-lg p-4 border border-green-500/20">
          <h5 className="text-white font-medium mb-2">✓ Mathematical Robustness</h5>
          <p className="text-gray-300 text-sm">Predictable interference-resistant channels based on harmonic series</p>
        </div>
        <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-lg p-4 border border-purple-500/20">
          <h5 className="text-white font-medium mb-2">✓ Infinite Scalability</h5>
          <p className="text-gray-300 text-sm">Add unlimited devices by assigning new harmonic channels</p>
        </div>
      </div>
    </div>
  );
}
