import type { FastifyInstance } from 'fastify'
import { prisma } from '../db'

async function databaseIsReachable(): Promise<boolean> {
  try {
    await prisma.$queryRaw`SELECT 1`
    return true
  } catch {
    return false
  }
}

export async function healthRoutes(app: FastifyInstance) {
  // Liveness: o processo está de pé. Não consulta o banco, para que uma queda
  // do PostgreSQL não faça o orquestrador reiniciar contêineres saudáveis.
  app.get('/livez', {
    schema: {
      tags: ['health'],
      summary: 'Liveness probe (processo vivo)',
      response: {
        200: {
          type: 'object',
          properties: { status: { type: 'string' } },
        },
      },
    },
  }, async (_req, reply) => {
    reply.send({ status: 'ok' })
  })

  // Readiness: a API consegue atender operações que dependem do banco.
  // Responde 503 quando o PostgreSQL está indisponível.
  app.get('/readyz', {
    schema: {
      tags: ['health'],
      summary: 'Readiness probe (banco acessível)',
      response: {
        200: {
          type: 'object',
          properties: { status: { type: 'string' }, database: { type: 'string' } },
        },
        503: {
          type: 'object',
          properties: { status: { type: 'string' }, database: { type: 'string' } },
        },
      },
    },
  }, async (_req, reply) => {
    const ok = await databaseIsReachable()
    reply
      .code(ok ? 200 : 503)
      .send({ status: ok ? 'ok' : 'unavailable', database: ok ? 'ok' : 'unavailable' })
  })

  // Compatibilidade com o endpoint existente: agora responde 503 quando o
  // banco está fora, em vez de 200 com status "ok".
  app.get('/health', {
    schema: {
      tags: ['health'],
      summary: 'Health check detalhado',
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
        503: {
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
    const ok = await databaseIsReachable()
    reply.code(ok ? 200 : 503).send({
      status: ok ? 'ok' : 'degraded',
      uptime: process.uptime(),
      timestamp: new Date().toISOString(),
      database: ok ? 'ok' : 'unavailable',
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
