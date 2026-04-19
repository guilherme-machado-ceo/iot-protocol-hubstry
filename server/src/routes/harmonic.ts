import type { FastifyInstance } from 'fastify'
import { z } from 'zod'
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

const SimulateBody = z.object({
  fundamentalFreq: z.number().positive().default(1000),
  channels: z.array(z.number().int().min(1).max(16)).default([2, 3, 4, 5, 7, 8]),
  message: z.string().max(256).optional(),
})

export async function harmonicRoutes(app: FastifyInstance) {
  app.post('/simulate', {
    schema: {
      tags: ['harmonic'],
      summary: 'Simulate harmonic protocol encoding',
      body: {
        type: 'object',
        properties: {
          fundamentalFreq: { type: 'number', default: 1000 },
          channels: { type: 'array', items: { type: 'integer' } },
          message: { type: 'string' },
        },
      },
    },
  }, async (req, reply) => {
    const body = SimulateBody.parse(req.body)
    const { fundamentalFreq, channels, message } = body

    const harmonics = channels.map((n) => ({
      channel: n,
      frequency: fundamentalFreq * n,
      label: channelLabel(n),
      encodedValue: message ? encodeHarmonic(message, n, fundamentalFreq) : null,
    }))

    await prisma.harmonicProtocolLog.create({
      data: {
        fundamentalFreq,
        channels: JSON.stringify(channels),
        message: message ?? null,
      },
    })

    reply.send({
      fundamentalFreq,
      harmonics,
      timestamp: new Date().toISOString(),
    })
  })

  app.post('/fft', {
    schema: {
      tags: ['harmonic'],
      summary: 'Compute FFT spectrum for a harmonic signal',
      body: {
        type: 'object',
        required: ['fundamentalFreq', 'channels'],
        properties: {
          fundamentalFreq: { type: 'number' },
          channels: { type: 'array', items: { type: 'integer' } },
          sampleRate: { type: 'number', default: 44100 },
          duration: { type: 'number', default: 0.1 },
        },
      },
    },
  }, async (req, reply) => {
    const { fundamentalFreq = 1000, channels = [2, 3, 4], sampleRate = 44100, duration = 0.1 } =
      req.body as Record<string, number | number[]>

    const freqs = (channels as number[]).map((n) => ({
      harmonic: n,
      frequency: (fundamentalFreq as number) * n,
      amplitude: 1 / n,
    }))

    reply.send({
      fundamentalFreq,
      sampleRate,
      duration,
      spectrum: freqs,
      timestamp: new Date().toISOString(),
    })
  })
}

function channelLabel(n: number): string {
  const labels: Record<number, string> = {
    1: 'FUNDAMENTAL',
    2: 'CONTROL',
    3: 'SENSOR_TEMP',
    4: 'SENSOR_HUMIDITY',
    5: 'ACTUATOR_LED',
    7: 'SECURITY',
    8: 'DATA_STREAM',
  }
  return labels[n] ?? `HARMONIC_${n}`
}

function encodeHarmonic(message: string, channel: number, f0: number): number {
  const freq = f0 * channel
  let hash = 0
  for (let i = 0; i < message.length; i++) {
    hash = (hash * 31 + message.charCodeAt(i)) >>> 0
  }
  return parseFloat((freq + (hash % 100) * 0.01).toFixed(4))
}
