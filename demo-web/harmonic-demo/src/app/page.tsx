'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Play, Pause, Wifi, Radio, Bluetooth, Shield, Activity, Zap } from 'lucide-react';
import HarmonicVisualizer from '@/components/HarmonicVisualizer';
import DeviceSimulator from '@/components/DeviceSimulator';
import ProtocolMetrics from '@/components/ProtocolMetrics';

export default function Home() {
  const [isSimulating, setIsSimulating] = useState(false);
  const [fundamentalFreq, setFundamentalFreq] = useState(1000);
  const [activeChannels, setActiveChannels] = useState<number[]>([]);

  useEffect(() => {
    if (isSimulating) {
      const interval = setInterval(() => {
        // Simulate random device activity
        const channels = [2, 3, 4, 5, 7, 8];
        const randomChannels = channels.filter(() => Math.random() > 0.7);
        setActiveChannels(randomChannels);
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [isSimulating]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <header className="border-b border-purple-500/20 bg-black/20 backdrop-blur-sm">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center space-x-3"
            >
              <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Harmonic IoT Protocol</h1>
                <p className="text-purple-300 text-sm">Hubstry Deep Tech</p>
              </div>
            </motion.div>
            
            <motion.div 
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center space-x-4"
            >
              <div className="text-right">
                <p className="text-white font-semibold">f₀ = {fundamentalFreq} Hz</p>
                <p className="text-purple-300 text-sm">Fundamental Frequency</p>
              </div>
              <button
                onClick={() => setIsSimulating(!isSimulating)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all ${
                  isSimulating 
                    ? 'bg-red-500 hover:bg-red-600 text-white' 
                    : 'bg-green-500 hover:bg-green-600 text-white'
                }`}
              >
                {isSimulating ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                <span>{isSimulating ? 'Stop' : 'Start'} Simulation</span>
              </button>
            </motion.div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        {/* Protocol Overview */}
        <motion.section 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="bg-black/30 backdrop-blur-sm rounded-xl border border-purple-500/20 p-6">
            <h2 className="text-xl font-bold text-white mb-4">Protocol Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="flex items-center space-x-3 p-4 bg-blue-500/10 rounded-lg border border-blue-500/20">
                <Wifi className="w-6 h-6 text-blue-400" />
                <div>
                  <p className="text-white font-medium">Wi-Fi</p>
                  <p className="text-blue-300 text-sm">H10-H15</p>
                </div>
              </div>
              <div className="flex items-center space-x-3 p-4 bg-green-500/10 rounded-lg border border-green-500/20">
                <Radio className="w-6 h-6 text-green-400" />
                <div>
                  <p className="text-white font-medium">LoRa</p>
                  <p className="text-green-300 text-sm">H2-H6</p>
                </div>
              </div>
              <div className="flex items-center space-x-3 p-4 bg-purple-500/10 rounded-lg border border-purple-500/20">
                <Bluetooth className="w-6 h-6 text-purple-400" />
                <div>
                  <p className="text-white font-medium">BLE</p>
                  <p className="text-purple-300 text-sm">H7-H9</p>
                </div>
              </div>
              <div className="flex items-center space-x-3 p-4 bg-red-500/10 rounded-lg border border-red-500/20">
                <Shield className="w-6 h-6 text-red-400" />
                <div>
                  <p className="text-white font-medium">Security</p>
                  <p className="text-red-300 text-sm">H16+</p>
                </div>
              </div>
            </div>
          </div>
        </motion.section>

        {/* Main Dashboard */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Harmonic Visualizer */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <HarmonicVisualizer 
              fundamentalFreq={fundamentalFreq}
              activeChannels={activeChannels}
              isSimulating={isSimulating}
            />
          </motion.div>

          {/* Device Simulator */}
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
          >
            <DeviceSimulator 
              fundamentalFreq={fundamentalFreq}
              onChannelActivity={(channels) => setActiveChannels(channels)}
              isSimulating={isSimulating}
            />
          </motion.div>
        </div>

        {/* Protocol Metrics */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="mt-8"
        >
          <ProtocolMetrics 
            activeChannels={activeChannels}
            isSimulating={isSimulating}
          />
        </motion.div>
      </main>

      {/* Footer */}
      <footer className="border-t border-purple-500/20 bg-black/20 backdrop-blur-sm mt-16">
        <div className="container mx-auto px-6 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between">
            <div className="text-center md:text-left mb-4 md:mb-0">
              <p className="text-white font-semibold">Harmonic IoT Protocol</p>
              <p className="text-purple-300">Mathematical Innovation for IoT Communication</p>
            </div>
            <div className="flex items-center space-x-6">
              <a 
                href="mailto:guilherme.ceo@hubstry.com"
                className="text-purple-300 hover:text-white transition-colors"
              >
                Contact for Investment
              </a>
              <div className="flex items-center space-x-2">
                <Zap className="w-4 h-4 text-yellow-400" />
                <span className="text-white text-sm">Powered by Hubstry Deep Tech</span>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
