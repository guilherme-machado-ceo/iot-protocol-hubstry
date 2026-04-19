import type { FastifyInstance } from 'fastify'
import { z } from 'zod'
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

const RegisterBody = z.object({
  deviceId: z.string().min(1).max(128),
  deviceType: z.string().default('generic'),
  fundamentalFreq: z.number().positive().default(1000),
  sensors: z.array(z.string()).default([]),
  harmonicChannels: z.record(z.string()).default({}),
  capabilities: z.array(z.string()).default([]),
})

export async function deviceRoutes(app: FastifyInstance) {
  app.post('/register', {
    schema: {
      tags: ['devices'],
      summary: 'Register a new IoT device',
      body: {
        type: 'object',
        required: ['deviceId'],
        properties: {
          deviceId: { type: 'string' },
          deviceType: { type: 'string' },
          fundamentalFreq: { type: 'number' },
          sensors: { type: 'array', items: { type: 'string' } },
          harmonicChannels: { type: 'object' },
          capabilities: { type: 'array', items: { type: 'string' } },
        },
      },
    },
  }, async (req, reply) => {
    const body = RegisterBody.parse(req.body)

    const device = await prisma.device.upsert({
      where: { deviceId: body.deviceId },
      update: {
        deviceType: body.deviceType,
        fundamentalFreq: body.fundamentalFreq,
        sensors: JSON.stringify(body.sensors),
        harmonicChannels: JSON.stringify(body.harmonicChannels),
        capabilities: JSON.stringify(body.capabilities),
        lastSeen: new Date(),
      },
      create: {
        deviceId: body.deviceId,
        deviceType: body.deviceType,
        fundamentalFreq: body.fundamentalFreq,
        sensors: JSON.stringify(body.sensors),
        harmonicChannels: JSON.stringify(body.harmonicChannels),
        capabilities: JSON.stringify(body.capabilities),
      },
    })

    reply.code(201).send({
      registered: true,
      deviceId: device.deviceId,
      networkFrequency: device.fundamentalFreq,
      timestamp: new Date().toISOString(),
    })
  })

  app.get('/', {
    schema: {
      tags: ['devices'],
      summary: 'List all registered devices',
    },
  }, async (_req, reply) => {
    const devices = await prisma.device.findMany({
      orderBy: { lastSeen: 'desc' },
      take: 100,
    })
    reply.send({ devices, total: devices.length })
  })

  app.get('/:deviceId', {
    schema: {
      tags: ['devices'],
      summary: 'Get device by ID',
      params: {
        type: 'object',
        properties: { deviceId: { type: 'string' } },
      },
    },
  }, async (req, reply) => {
    const { deviceId } = req.params as { deviceId: string }
    const device = await prisma.device.findUnique({ where: { deviceId } })
    if (!device) {
      return reply.code(404).send({ error: 'Device not found' })
    }
    reply.send(device)
  })
}
