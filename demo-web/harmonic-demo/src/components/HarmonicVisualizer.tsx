'use client';

import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';

interface HarmonicVisualizerProps {
  fundamentalFreq: number;
  activeChannels: number[];
  isSimulating: boolean;
}

export default function HarmonicVisualizer({ fundamentalFreq, activeChannels, isSimulating }: HarmonicVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [harmonicData, setHarmonicData] = useState<{ channel: number; frequency: number; amplitude: number }[]>([]);

  useEffect(() => {
    if (isSimulating) {
      const interval = setInterval(() => {
        const newData = activeChannels.map(channel => ({
          channel,
          frequency: fundamentalFreq * channel,
          amplitude: 0.3 + Math.random() * 0.7
        }));
        setHarmonicData(newData);
      }, 100);

      return () => clearInterval(interval);
    } else {
      setHarmonicData([]);
    }
  }, [isSimulating, activeChannels, fundamentalFreq]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Clear canvas
    ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
    ctx.fillRect(0, 0, width, height);

    // Draw grid
    ctx.strokeStyle = 'rgba(147, 51, 234, 0.2)';
    ctx.lineWidth = 1;
    
    // Vertical grid lines
    for (let i = 0; i <= 10; i++) {
      const x = (width / 10) * i;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }

    // Horizontal grid lines
    for (let i = 0; i <= 8; i++) {
      const y = (height / 8) * i;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    // Draw harmonic frequencies
    harmonicData.forEach((harmonic) => {
      const x = (harmonic.channel / 20) * width;
      const barHeight = harmonic.amplitude * (height * 0.8);
      const y = height - barHeight;

      // Color based on channel type
      let color = 'rgba(147, 51, 234, 0.8)'; // Purple default
      if (harmonic.channel >= 2 && harmonic.channel <= 6) color = 'rgba(34, 197, 94, 0.8)'; // Green for LoRa
      if (harmonic.channel >= 7 && harmonic.channel <= 9) color = 'rgba(147, 51, 234, 0.8)'; // Purple for BLE
      if (harmonic.channel >= 10 && harmonic.channel <= 15) color = 'rgba(59, 130, 246, 0.8)'; // Blue for Wi-Fi
      if (harmonic.channel >= 16) color = 'rgba(239, 68, 68, 0.8)'; // Red for Security

      // Draw bar
      ctx.fillStyle = color;
      ctx.fillRect(x - 10, y, 20, barHeight);

      // Draw frequency label
      ctx.fillStyle = 'white';
      ctx.font = '12px monospace';
      ctx.textAlign = 'center';
      ctx.fillText(`H${harmonic.channel}`, x, height - 5);
      ctx.fillText(`${harmonic.frequency}Hz`, x, y - 5);
    });

    // Draw fundamental frequency line
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(0, height - 20);
    ctx.lineTo(width, height - 20);
    ctx.stroke();
    ctx.setLineDash([]);

    // Label fundamental frequency
    ctx.fillStyle = 'white';
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`f₀ = ${fundamentalFreq} Hz`, 10, height - 25);

  }, [harmonicData, fundamentalFreq]);

  return (
    <div className="bg-black/30 backdrop-blur-sm rounded-xl border border-purple-500/20 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-white">Harmonic Spectrum Analysis</h3>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-green-400 text-sm">Live FFT</span>
        </div>
      </div>
      
      <div className="relative">
        <canvas
          ref={canvasRef}
          width={600}
          height={300}
          className="w-full h-[300px] bg-black/50 rounded-lg border border-purple-500/10"
        />
        
        {!isSimulating && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-lg">
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                >
                  <div className="w-8 h-8 bg-purple-400 rounded-full animate-pulse"></div>
                </motion.div>
              </div>
              <p className="text-white font-medium">Start simulation to see harmonic activity</p>
              <p className="text-purple-300 text-sm">Real-time FFT analysis of harmonic channels</p>
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-green-500 rounded"></div>
          <span className="text-green-300">LoRa (H2-H6)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-purple-500 rounded"></div>
          <span className="text-purple-300">BLE (H7-H9)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-blue-500 rounded"></div>
          <span className="text-blue-300">Wi-Fi (H10-H15)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-red-500 rounded"></div>
          <span className="text-red-300">Security (H16+)</span>
        </div>
      </div>
    </div>
  );
}
