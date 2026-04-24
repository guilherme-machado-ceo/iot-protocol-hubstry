import Fastify from 'fastify'
import cors from '@fastify/cors'
import helmet from '@fastify/helmet'
import swagger from '@fastify/swagger'
import swaggerUi from '@fastify/swagger-ui'
import { healthRoutes } from './routes/health'
import { harmonicRoutes } from './routes/harmonic'
import { deviceRoutes } from './routes/devices'

const server = Fastify({
  logger: {
    level: process.env.LOG_LEVEL ?? 'info',
  },
})

async function build() {
  await server.register(helmet)
  await server.register(cors, {
    origin: process.env.CORS_ORIGIN ?? '*',
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
  const app = await build()
  const port = parseInt(process.env.PORT ?? '3001', 10)
  const host = process.env.HOST ?? '0.0.0.0'

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
