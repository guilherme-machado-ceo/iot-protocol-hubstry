import type { FastifyInstance } from 'fastify'
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

export async function healthRoutes(app: FastifyInstance) {
  app.get('/health', {
    schema: {
      tags: ['health'],
      summary: 'Health check',
      response: {
        200: {
          type: 'object',
          properties: {
            status: { type: 'string' },
            uptime: { type: 'number' },
            timestamp: { type: 'string' },
            database: { type: 'string' },
          },
        },
      },
    },
  }, async (_req, reply) => {
    let dbStatus = 'ok'
    try {
      await prisma.$queryRaw`SELECT 1`
    } catch {
      dbStatus = 'unavailable'
    }

    reply.send({
      status: 'ok',
      uptime: process.uptime(),
      timestamp: new Date().toISOString(),
      database: dbStatus,
    })
  })

  app.get('/metrics', {
    schema: {
      tags: ['health'],
      summary: 'Prometheus-compatible metrics (text format)',
      produces: ['text/plain'],
    },
  }, async (_req, reply) => {
    const uptime = process.uptime()
    const memUsage = process.memoryUsage()

    const metrics = [
      `# HELP harmonic_uptime_seconds Server uptime in seconds`,
      `# TYPE harmonic_uptime_seconds gauge`,
      `harmonic_uptime_seconds ${uptime.toFixed(2)}`,
      `# HELP harmonic_memory_rss_bytes Resident set size in bytes`,
      `# TYPE harmonic_memory_rss_bytes gauge`,
      `harmonic_memory_rss_bytes ${memUsage.rss}`,
    ].join('\n')

    reply.type('text/plain').send(metrics)
  })
}
