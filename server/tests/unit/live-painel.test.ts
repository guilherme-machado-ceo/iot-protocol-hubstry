import Fastify from 'fastify'
import helmet from '@fastify/helmet'
import { writeFileSync } from 'node:fs'
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Observacao } from '../../src/live/tipos'

// Banco simulado: só o que o painel consulta.
const estado: { runs: any[]; obs: any[]; consultas: string[] } = { runs: [], obs: [], consultas: [] }
vi.mock('../../src/db', () => ({
  prisma: {
    liveRun: {
      findFirst: vi.fn(async ({ where }: any = {}) => {
        let r = [...estado.runs].sort((a, b) => b.slotUtc - a.slotUtc)
        if (where?.status?.in) r = r.filter((x) => where.status.in.includes(x.status))
        if (where?.measuredSnrDb) r = r.filter((x) => x.measuredSnrDb != null)
        return r[0] ?? null
      }),
      findMany: vi.fn(async () => [...estado.runs].sort((a, b) => b.slotUtc - a.slotUtc).slice(0, 12)),
    },
    liveObservation: {
      findFirst: vi.fn(async ({ where }: any) => {
        const r = estado.obs.filter((o) => o.provider === where.provider && o.stationRef === where.stationRef && o.parameter === where.parameter)
        return r.sort((a, b) => b.observedAt - a.observedAt)[0] ?? null
      }),
    },
    $queryRaw: vi.fn(async (partes: TemplateStringsArray) => {
      estado.consultas.push(partes.join('?'))
      return Array.from({ length: 1500 }, (_, i) => ({ t: new Date(Date.now() - i * 60_000), v: i }))
    }),
  },
}))

const { liveRoutes, limparCache, DECLARACAO } = await import('../../src/routes/live')
const { executarProtocolo, CHAVES_SERIES } = await import('../../src/live/protocolo')
const app = Fastify()

function obs(chave: string, value: number, unit: string, minutosAtras: number): Observacao {
  const [provider, stationRef, parameter] = chave.split(':')
  return { provider: provider as 'openaq' | 'ons', stationRef, sensorRef: `${stationRef}-${parameter}`, parameter, value, unit,
    observedAt: new Date(Date.now() - minutosAtras * 60_000), locality: provider === 'ons' ? null : 'Cidade Exemplo',
    licenseName: provider === 'ons' ? 'CC BY 4.0' : 'US Public Domain', licenseUrl: 'https://exemplo.org/licenca',
    attribution: provider === 'ons' ? 'ONS' : 'AirNow', sourceUrl: 'https://exemplo.org/fonte' }
}

function popular(minutosDesdeOk: number, ultimaFalhou = false) {
  const valores: Record<string, [number, string]> = { pm25: [12.4, 'µg/m³'], pm10: [30, 'µg/m³'], o3: [0.031, 'ppm'], no2: [0.012, 'ppm'],
    carga: [72000, 'MWmed'], geracao_hidraulica: [41000, 'MWmed'], geracao_eolica: [12000, 'MWmed'], geracao_solar: [9000, 'MWmed'] }
  estado.obs = CHAVES_SERIES.map((c) => { const [v, u] = valores[c.split(':')[2]]; return obs(c, v, u, 90) })
  const slot = new Date(Date.now() - minutosDesdeOk * 60_000)
  const p = executarProtocolo(estado.obs, slot.toISOString())
  estado.runs = [{ id: 1, slotUtc: slot, status: 'succeeded', newObservations: 12, completedAt: slot, ...p }]
  if (ultimaFalhou) estado.runs.push({ id: 2, slotUtc: new Date(), status: 'failed', newObservations: 0, completedAt: new Date(), measuredSnrDb: null })
}

beforeAll(async () => {
  await app.register(helmet)
  await app.register(liveRoutes)
  await app.ready()
})
beforeEach(() => { limparCache(); estado.consultas = [] })

describe('painel /live', () => {
  it('serve a página com a declaração obrigatória, o selo e a logo, e CSP sem script inline', async () => {
    const r = await app.inject({ method: 'GET', url: '/live' })
    expect(r.statusCode).toBe(200)
    expect(r.headers['content-type']).toContain('text/html')
    expect(r.body).toContain(DECLARACAO)
    expect(r.body).toContain('nvidia-inception.svg')
    expect(r.body).toContain('hubstry-logo-claro.png')
    expect(r.body).not.toMatch(/<script>(?!<\/script>)/)
    expect(String(r.headers['content-security-policy'])).toContain("script-src 'self'")
  })

  it('serve JS, CSS e marcas com o tipo certo; arquivo fora da lista dá 404', async () => {
    expect((await app.inject('/live/app.js')).headers['content-type']).toContain('javascript')
    expect((await app.inject('/live/app.css')).headers['content-type']).toContain('text/css')
    expect((await app.inject('/live/assets/nvidia-inception.svg')).headers['content-type']).toBe('image/svg+xml')
    expect((await app.inject('/live/assets/favicon-32.png')).headers['content-type']).toBe('image/png')
    expect((await app.inject('/live/assets/..%2F..%2Fpackage.json')).statusCode).toBe(404)
    expect((await app.inject('/live/index.ts')).statusCode).toBe(404)
  })
})

describe('GET /api/live/public', () => {
  it('estado normal: métricas, leituras com licença e declaração; sem coordenadas', async () => {
    popular(3)
    const r = await app.inject('/api/live/public')
    expect(r.statusCode).toBe(200)
    const d = r.json()
    if (process.env.PAINEL_FIXTURE) writeFileSync(process.env.PAINEL_FIXTURE, r.body)
    expect(d.estado).toBe('normal')
    expect(d.declaracao).toBe(DECLARACAO)
    expect(d.leituras).toHaveLength(12)
    expect(d.leituras[0]).toMatchObject({ licenseName: expect.any(String), licenseUrl: expect.any(String), natureza: expect.any(String) })
    expect(d.protocolo.metricas.execucao.recall).toBe(1)
    expect(d.protocolo.mqtt.payloadBytes).toBeGreaterThan(0)
    expect(r.body).not.toMatch(/latitude|longitude|coordinates|errorDetail|stack/i)
  })

  it('leitura antiga demais some da tabela; as demais trazem a idade em horas', async () => {
    popular(3)
    estado.obs[2] = { ...estado.obs[2], observedAt: new Date('2016-03-10T09:00:00Z') }
    const d = (await app.inject('/api/live/public')).json()
    expect(d.leituras).toHaveLength(11)
    expect(d.leituras.find((l: any) => l.chave === CHAVES_SERIES[2])).toBeUndefined()
    expect(d.leituras[0].idadeHoras).toBeCloseTo(1.5, 1)
  })

  it('marca desatualizado quando a última execução ok tem mais de 15 minutos', async () => {
    popular(20)
    expect((await app.inject('/api/live/public')).json().estado).toBe('desatualizado')
  })

  it('marca falha quando a execução mais recente falhou', async () => {
    popular(3, true)
    const d = (await app.inject('/api/live/public')).json()
    expect(d.estado).toBe('falha')
    expect(d.protocolo).not.toBeNull()
  })

  it('série: no máximo 1.000 pontos; 7d e 30d agregam por hora', async () => {
    popular(3)
    const r = await app.inject(`/api/live/public?window=30d&series=${encodeURIComponent(CHAVES_SERIES[0])}`)
    expect(r.json().pontos.length).toBeLessThanOrEqual(1000)
    expect(estado.consultas.at(-1)).toContain("date_trunc('hour'")
  })

  it('recusa série desconhecida e janela inválida', async () => {
    expect((await app.inject('/api/live/public?series=openaq:999:pm25')).statusCode).toBe(400)
    expect((await app.inject('/api/live/public?window=1y')).statusCode).toBe(400)
  })
})
