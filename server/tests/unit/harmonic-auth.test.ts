import Fastify from 'fastify'
import { beforeAll, describe, expect, it, vi } from 'vitest'

// Aqui o middleware de autenticação é o REAL (requireScope); só o banco é simulado,
// com um repositório de chaves em memória. Cobre harmonic:write em /simulate,
// que o teste de contrato (harmonic-routes.test.ts) não exercita.
type Registro = { id: string; prefix: string; keyHash: string; scopes: string[]; revokedAt: Date | null; expiresAt: Date | null }
const chaves = new Map<string, Registro>()
const logs: unknown[] = []

vi.mock('../../src/db', () => ({
  prisma: {
    apiKey: {
      findUnique: vi.fn(async ({ where }: { where: { prefix: string } }) => chaves.get(where.prefix) ?? null),
      update: vi.fn(async () => ({})),
    },
    harmonicProtocolLog: { create: vi.fn(async (arg: unknown) => { logs.push(arg); return arg }) },
  },
}))

const { generateKey } = await import('../../src/keys')
const { harmonicRoutes } = await import('../../src/routes/harmonic')
const app = Fastify()

function novaChave(scopes: string[], extra: Partial<Registro> = {}): string {
  const { key, prefix, keyHash } = generateKey()
  chaves.set(prefix, { id: prefix, prefix, keyHash, scopes, revokedAt: null, expiresAt: null, ...extra })
  return key
}

const SIM = { method: 'POST' as const, url: '/api/harmonic/simulate', payload: { harmonics: [{ a: 3, b: 2 }] } }

beforeAll(async () => {
  await app.register(harmonicRoutes, { prefix: '/api/harmonic' })
  await app.ready()
})

describe('POST /simulate exige harmonic:write (autenticação real)', () => {
  it('sem chave: 401 e nada registrado', async () => {
    const antes = logs.length
    const r = await app.inject(SIM)
    expect(r.statusCode).toBe(401)
    expect(logs.length).toBe(antes)
  })

  it('chave malformada: 401', async () => {
    const r = await app.inject({ ...SIM, headers: { 'x-api-key': 'nk_curta' } })
    expect(r.statusCode).toBe(401)
  })

  it('chave com formato válido mas desconhecida: 401', async () => {
    const { key } = generateKey()
    const r = await app.inject({ ...SIM, headers: { 'x-api-key': key } })
    expect(r.statusCode).toBe(401)
  })

  it('chave só com harmonic:compute: 403 e nada registrado', async () => {
    const antes = logs.length
    const r = await app.inject({ ...SIM, headers: { 'x-api-key': novaChave(['harmonic:compute']) } })
    expect(r.statusCode).toBe(403)
    expect(r.json().message).toContain('harmonic:write')
    expect(logs.length).toBe(antes)
  })

  it('chave com escopos de dispositivos não serve para /simulate: 403', async () => {
    const r = await app.inject({ ...SIM, headers: { 'x-api-key': novaChave(['devices:read', 'devices:write']) } })
    expect(r.statusCode).toBe(403)
  })

  it('chave com harmonic:write: 200 e simulação registrada', async () => {
    const antes = logs.length
    const r = await app.inject({ ...SIM, headers: { 'x-api-key': novaChave(['harmonic:write']) } })
    expect(r.statusCode).toBe(200)
    expect(r.json().components[0].ratio).toBe('3/2')
    expect(logs.length).toBe(antes + 1)
  })

  it('harmonic:write também via Authorization: Bearer', async () => {
    const r = await app.inject({ ...SIM, headers: { authorization: `Bearer ${novaChave(['harmonic:write'])}` } })
    expect(r.statusCode).toBe(200)
  })

  it('chave revogada: 401', async () => {
    const r = await app.inject({ ...SIM, headers: { 'x-api-key': novaChave(['harmonic:write'], { revokedAt: new Date() }) } })
    expect(r.statusCode).toBe(401)
    expect(r.json().message).toContain('revogada')
  })

  it('chave expirada: 401', async () => {
    const r = await app.inject({ ...SIM, headers: { 'x-api-key': novaChave(['harmonic:write'], { expiresAt: new Date(Date.now() - 1000) }) } })
    expect(r.statusCode).toBe(401)
    expect(r.json().message).toContain('expirada')
  })

  it('segredo adulterado com prefixo válido: 401', async () => {
    const key = novaChave(['harmonic:write'])
    const adulterada = key.slice(0, -1) + (key.endsWith('A') ? 'B' : 'A')
    const r = await app.inject({ ...SIM, headers: { 'x-api-key': adulterada } })
    expect(r.statusCode).toBe(401)
  })
})

describe('harmonic:write não dá acesso às rotas de cálculo', () => {
  it('GET /hn com harmonic:write: 403', async () => {
    const r = await app.inject({ method: 'GET', url: '/api/harmonic/hn', headers: { 'x-api-key': novaChave(['harmonic:write']) } })
    expect(r.statusCode).toBe(403)
  })

  it('GET /hn com harmonic:compute: 200', async () => {
    const r = await app.inject({ method: 'GET', url: '/api/harmonic/hn', headers: { 'x-api-key': novaChave(['harmonic:compute']) } })
    expect(r.statusCode).toBe(200)
  })
})
