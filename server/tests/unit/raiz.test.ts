import { describe, expect, it, vi } from 'vitest'

vi.mock('../../src/db', () => ({ prisma: {}, disconnectPrisma: vi.fn() }))

describe('raiz da API', () => {
  it('GET / redireciona para o painel /live', async () => {
    const { build } = await import('../../src/index')
    const app = await build()
    const r = await app.inject({ method: 'GET', url: '/' })
    expect(r.statusCode).toBe(302)
    expect(r.headers.location).toBe('/live')
    await app.close()
  })
})
