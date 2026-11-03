import Fastify from 'fastify'
import { beforeAll, describe, expect, it, vi } from 'vitest'

// Banco e autenticação simulados: aqui só se testa o contrato H16 das rotas.
const logs: unknown[] = []
vi.mock('../../src/db', () => ({
  prisma: { harmonicProtocolLog: { create: vi.fn(async (arg: unknown) => { logs.push(arg); return arg }) } },
}))
vi.mock('../../src/auth', () => ({ requireScope: () => async () => undefined }))

const { harmonicRoutes } = await import('../../src/routes/harmonic')
const app = Fastify()

beforeAll(async () => {
  await app.register(harmonicRoutes, { prefix: '/api/harmonic' })
  await app.ready()
})

describe('rotas do protocolo harmônico (contrato H16)', () => {
  it('GET /hn devolve |H16| = 159', async () => {
    const r = await app.inject({ method: 'GET', url: '/api/harmonic/hn' })
    expect(r.statusCode).toBe(200)
    expect(r.json().cardinality).toBe(159)
  })

  it('GET /channels devolve os 12 canais do HPM 1.0', async () => {
    const r = await app.inject({ method: 'GET', url: '/api/harmonic/channels' })
    expect(r.json().channels).toHaveLength(12)
    expect(r.json().channels[2]).toMatchObject({ ratio: '3/2', frequency_hz: 24576 })
  })

  it('POST /simulate usa (a/b)·f0 e registra as razões', async () => {
    const r = await app.inject({ method: 'POST', url: '/api/harmonic/simulate', payload: { f0: 1000, harmonics: [{ a: 3, b: 2 }, { a: 7, b: 4 }] } })
    expect(r.statusCode).toBe(200)
    expect(r.json().components.map((c: { frequency_hz: number }) => c.frequency_hz)).toEqual([1500, 1750])
    expect(JSON.stringify(logs.at(-1))).toContain('{\\"a\\":3,\\"b\\":2}')
  })

  it('POST /simulate recusa razão fora de H16 com 400', async () => {
    const r = await app.inject({ method: 'POST', url: '/api/harmonic/simulate', payload: { harmonics: [{ a: 4, b: 2 }] } })
    expect(r.statusCode).toBe(400)
    expect(r.json().message).toContain('4/2')
  })

  it('POST /simulate recusa channels e harmonics juntos', async () => {
    const r = await app.inject({ method: 'POST', url: '/api/harmonic/simulate', payload: { channels: [1], harmonics: [{ a: 1, b: 1 }] } })
    expect(r.statusCode).toBe(400)
  })

  it('POST /fft decodifica os 6 primeiros canais do HPM 1.0 com os padrões', async () => {
    const r = await app.inject({ method: 'POST', url: '/api/harmonic/fft', payload: {} })
    expect(r.statusCode).toBe(200)
    const ratios = r.json().peaks.map((p: { closest_ratio: string }) => p.closest_ratio).sort()
    expect(ratios).toEqual(['1/1', '2/1', '3/1', '3/2', '4/3', '5/4'])
  })

  it('POST /fft recusa componentes acima de Nyquist (o núcleo Python faria aliasing)', async () => {
    const r = await app.inject({ method: 'POST', url: '/api/harmonic/fft', payload: { sampleRate: 44100, duration: 0.01 } })
    expect(r.statusCode).toBe(400)
    expect(r.json().message).toContain('Nyquist')
  })

  it('POST /fft limita o número de amostras', async () => {
    const r = await app.inject({ method: 'POST', url: '/api/harmonic/fft', payload: { sampleRate: 1e6, duration: 1 } })
    expect(r.statusCode).toBe(400)
  })
})
