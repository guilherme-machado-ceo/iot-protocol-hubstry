import Fastify from 'fastify'
import cors from '@fastify/cors'
import helmet from '@fastify/helmet'
import swagger from '@fastify/swagger'
import swaggerUi from '@fastify/swagger-ui'
import { healthRoutes } from './routes/health'
import { harmonicRoutes } from './routes/harmonic'
import { deviceRoutes } from './routes/devices'
import { disconnectPrisma } from './db'

const server = Fastify({
  logger: {
    level: process.env.LOG_LEVEL ?? 'info',
  },
})

// CORS: em produção a origem precisa ser explícita (CORS_ORIGIN).
// Aceita lista separada por vírgula. Sem a variável, só libera tudo fora de produção.
function resolveCorsOrigin(): string | string[] | boolean {
  const raw = process.env.CORS_ORIGIN?.trim()
  if (raw) {
    const origins = raw.split(',').map((o) => o.trim()).filter(Boolean)
    return origins.length === 1 ? origins[0] : origins
  }
  if (process.env.NODE_ENV === 'production') {
    throw new Error('CORS_ORIGIN é obrigatória em produção (ex.: https://nautam.hubstry.dev)')
  }
  return true
}

async function build() {
  await server.register(helmet)
  await server.register(cors, {
    origin: resolveCorsOrigin(),
  })

  await server.register(swagger, {
    openapi: {
      info: {
        title: 'Harmonic IoT Protocol API',
        description: 'REST API for the Harmonic IoT Protocol server',
        version: '1.0.0',
      },
      tags: [
        { name: 'health', description: 'Health and readiness endpoints' },
        { name: 'harmonic', description: 'Harmonic protocol simulation' },
        { name: 'devices', description: 'Device registration and management' },
      ],
    },
  })

  await server.register(swaggerUi, {
    routePrefix: '/docs',
  })

  await server.register(healthRoutes, { prefix: '/api' })
  await server.register(harmonicRoutes, { prefix: '/api/harmonic' })
  await server.register(deviceRoutes, { prefix: '/api/devices' })

  return server
}

async function main() {
  let app: Awaited<ReturnType<typeof build>>
  try {
    app = await build()
  } catch (err) {
    server.log.error(err)
    process.exit(1)
  }
  const port = parseInt(process.env.PORT ?? '3001', 10)
  const host = process.env.HOST ?? '0.0.0.0'

  // Encerramento gracioso: o ECS envia SIGTERM antes de parar a tarefa.
  for (const signal of ['SIGTERM', 'SIGINT'] as const) {
    process.once(signal, async () => {
      app.log.info(`${signal} recebido, encerrando`)
      try {
        await app.close()
        await disconnectPrisma()
      } finally {
        process.exit(0)
      }
    })
  }

  try {
    await app.listen({ port, host })
    app.log.info(`Server listening on ${host}:${port}`)
    app.log.info(`Swagger docs at http://${host}:${port}/docs`)
  } catch (err) {
    app.log.error(err)
    process.exit(1)
  }
}

main()
