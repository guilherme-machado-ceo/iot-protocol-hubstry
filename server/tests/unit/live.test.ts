import { describe, expect, it } from 'vitest'
import { coletarOpenAQ } from '../../src/live/openaq'
import { coletarONS, instanteOnsParaUtc, interpretarCauda } from '../../src/live/ons'
import { executar, slotDe, type BancoLive } from '../../src/live/ingestao'
import type { Fetch } from '../../src/live/tipos'

const LIC_PD = { id: 33, name: 'US Public Domain', commercialUseAllowed: true, redistributionAllowed: true, attributionRequired: false, sourceUrl: 'http://www.usa.gov/publicdomain/label/1.0/' }
const LIC_NC = { id: 9, name: 'CC BY-NC', commercialUseAllowed: false, redistributionAllowed: true, attributionRequired: true, sourceUrl: 'x' }

function local(id: number, extra: Record<string, unknown> = {}) {
  return {
    id, locality: 'Houston', isMobile: false, isMonitor: true,
    provider: { name: 'AirNow' }, owner: { name: 'Gov' },
    coordinates: { latitude: 1, longitude: 2 }, // existe na API, não deve ser lido
    sensors: [{ id: id * 10, parameter: { name: 'pm25', units: 'µg/m³' } }, { id: id * 10 + 1, parameter: { name: 'o3', units: 'ppm' } }],
    licenses: [{ id: 33, dateTo: null }],
    ...extra,
  }
}

function fakeFetch(rotas: Record<string, unknown>, chamadas: string[] = []): Fetch {
  return (async (url: string | URL, init?: RequestInit) => {
    const u = String(url)
    chamadas.push(u + (init?.headers && (init.headers as Record<string, string>).Range ? ` [${(init.headers as Record<string, string>).Range}]` : ''))
    const chave = Object.keys(rotas).find((k) => u.endsWith(k))
    if (!chave) return new Response('nf', { status: 404 })
    const v = rotas[chave]
    return typeof v === 'string' ? new Response(v, { status: 206 }) : Response.json(v)
  }) as unknown as Fetch
}

const AGORA = new Date('2026-11-03T12:07:30Z')
const ultimas = (id: number) => ({ results: [
  { value: 12.5, sensorsId: id * 10, datetime: { utc: '2026-11-03T11:00:00Z' } },
  { value: 0.031, sensorsId: id * 10 + 1, datetime: { utc: '2026-11-03T11:00:00Z' } },
] })

describe('OpenAQ (fail-closed)', () => {
  it('aceita monitor fixo com licença comercial e não lê coordenadas', async () => {
    const f = fakeFetch({ '/locations/1': { results: [local(1)] }, '/licenses/33': { results: [LIC_PD] }, '/locations/1/latest': ultimas(1) })
    const r = await coletarOpenAQ('k', f, [{ location: 1, parameter: 'pm25' }, { location: 1, parameter: 'o3' }])
    expect(r.rejeitadas).toEqual([])
    expect(r.observacoes.map((o) => [o.parameter, o.value, o.unit])).toEqual([['pm25', 12.5, 'µg/m³'], ['o3', 0.031, 'ppm']])
    expect(JSON.stringify(r.observacoes)).not.toMatch(/latitude|longitude/)
    expect(r.observacoes[0].attribution).toBe('AirNow via OpenAQ')
  })

  it('recusa licença sem uso comercial, estação móvel e estação sem licença', async () => {
    const f = fakeFetch({
      '/locations/2': { results: [local(2, { licenses: [{ id: 9, dateTo: null }] })] }, '/licenses/9': { results: [LIC_NC] },
      '/locations/3': { results: [local(3, { isMobile: true })] },
      '/locations/4': { results: [local(4, { licenses: [] })] },
    })
    const r = await coletarOpenAQ('k', f, [{ location: 2, parameter: 'pm25' }, { location: 3, parameter: 'pm25' }, { location: 4, parameter: 'pm25' }])
    expect(r.observacoes).toEqual([])
    expect(r.rejeitadas.map((x) => x.motivo)).toEqual(['licença sem uso comercial ou redistribuição', 'móvel ou não é monitor', 'sem licença vigente'])
  })

  it('erro HTTP vira rejeição, sem derrubar as outras estações', async () => {
    const f = fakeFetch({ '/locations/1': { results: [local(1)] }, '/licenses/33': { results: [LIC_PD] }, '/locations/1/latest': ultimas(1) })
    const r = await coletarOpenAQ('k', f, [{ location: 99, parameter: 'pm25' }, { location: 1, parameter: 'pm25' }])
    expect(r.observacoes).toHaveLength(1)
    expect(r.rejeitadas[0].motivo).toContain('HTTP 404')
  })
})

const CAUDA = `.0;11371.368;11567.56
S  ;SUL;2026-10-31 23:00:00;13209.38;1066.19;361.858;0.0;11700.024;2937.404
SE ;SUDESTE/CENTRO-OESTE;2026-10-31 23:00:00;31617.295999999995;7036.925;201.886;0.0;41333.505;-2477.398
SIN;SISTEMA INTERLIGADO NACIONAL;2026-10-31 23:00:00;51080.512;11371.368;11567.566000000004;0.0;74019.45;0.0
`

describe('ONS', () => {
  it('segue o 301 do S3 para a região indicada em x-amz-bucket-region', async () => {
    const chamadas: string[] = []
    const f = (async (url: string | URL) => {
      const u = String(url); chamadas.push(u)
      if (u.includes('.s3.amazonaws.com/')) return new Response('<Error>PermanentRedirect</Error>', { status: 301, headers: { 'x-amz-bucket-region': 'us-west-2' } })
      if (u.includes('.s3.us-west-2.amazonaws.com/') && u.endsWith('_2026.csv')) return new Response(CAUDA, { status: 206 })
      return new Response('nf', { status: 404 })
    }) as unknown as Fetch
    const r = await coletarONS(f, AGORA)
    expect(r.rejeitadas).toEqual([])
    expect(r.observacoes).toHaveLength(4)
    expect(chamadas[1]).toContain('ons-aws-prod-opendata.s3.us-west-2.amazonaws.com/dataset/balanco_energia_subsistema_ho/')
  })

  it('horário de Brasília vira UTC (+3 h)', () => {
    expect(instanteOnsParaUtc('2026-10-31 23:00:00').toISOString()).toBe('2026-11-01T02:00:00.000Z')
  })

  it('lê a última linha do SIN e ignora a linha cortada do início da cauda', () => {
    const obs = interpretarCauda(CAUDA, 2026)
    expect(obs.map((o) => [o.parameter, o.value])).toEqual([
      ['carga', 74019.45], ['geracao_hidraulica', 51080.512], ['geracao_eolica', 11567.566000000004], ['geracao_solar', 0],
    ])
    expect(obs[0]).toMatchObject({ unit: 'MWmed', licenseName: 'CC BY 4.0', sensorRef: 'ons:SIN:val_carga' })
  })

  it('pede só o fim do arquivo (HTTP Range) e cai para o ano anterior na virada', async () => {
    const chamadas: string[] = []
    const f = fakeFetch({ 'BALANCO_ENERGIA_SUBSISTEMA_2025.csv': CAUDA }, chamadas)
    const r = await coletarONS(f, new Date('2026-01-01T03:10:00Z'))
    expect(r.observacoes).toHaveLength(4)
    expect(chamadas[0]).toContain('_2026.csv [bytes=-8192]')
    expect(chamadas[1]).toContain('_2025.csv')
  })
})

function bancoFalso() {
  const runs: { id: number; slotUtc: Date; [k: string]: unknown }[] = []
  const obs = new Map<string, unknown>()
  const db: BancoLive = {
    liveRun: {
      async create({ data }) {
        if (runs.some((r) => r.slotUtc.getTime() === data.slotUtc.getTime())) throw Object.assign(new Error('unique'), { code: 'P2002' })
        const r = { id: runs.length + 1, ...data }; runs.push(r); return r
      },
      async update({ where, data }) { Object.assign(runs.find((r) => r.id === where.id)!, data); return {} },
    },
    liveObservation: {
      async createMany({ data }) {
        let count = 0
        for (const o of data) { const k = `${o.provider}|${o.sensorRef}|${o.observedAt.toISOString()}`; if (!obs.has(k)) { obs.set(k, o); count++ } }
        return { count }
      },
    },
  }
  return { db, runs, obs }
}

describe('job de ingestão', () => {
  const rotas = { '/locations/162': { results: [local(162)] }, '/licenses/33': { results: [LIC_PD] }, '/locations/162/latest': ultimas(162), 'SUBSISTEMA_2026.csv': CAUDA }
  const so162 = { location: 162 }

  it('slot de 5 minutos', () => {
    expect(slotDe(AGORA).toISOString()).toBe('2026-11-03T12:05:00.000Z')
  })

  it('mesmo slot não roda duas vezes; leitura repetida não duplica', async () => {
    const { db, runs, obs } = bancoFalso()
    const f = fakeFetch(rotas)
    const a = await executar(db, { agora: AGORA, chaveOpenAQ: 'k', f })
    expect(a.status).toBe('succeeded')
    expect(a.novas).toBe(a.coletadas)
    const b = await executar(db, { agora: AGORA, chaveOpenAQ: 'k', f })
    expect(b.status).toBe('slot_ocupado')
    const c = await executar(db, { agora: new Date(AGORA.getTime() + 5 * 60_000), chaveOpenAQ: 'k', f })
    expect(c.status).toBe('no_new_data')
    expect(runs).toHaveLength(2)
    expect(obs.size).toBe(a.novas)
    void so162
  })

  it('sem chave da OpenAQ, segue só com o ONS e registra o motivo', async () => {
    const { db } = bancoFalso()
    const r = await executar(db, { agora: AGORA, f: fakeFetch(rotas) })
    expect(r.status).toBe('succeeded')
    expect(r.coletadas).toBe(4)
    expect(r.rejeitadas[0].motivo).toBe('OPENAQ_API_KEY ausente')
  })

  it('leitura antiga demais (estação parada) não entra no quadro nem no banco', async () => {
    const { db, obs } = bancoFalso()
    const depois = new Date(AGORA.getTime() + 10 * 24 * 3_600_000) // as fixtures ficam com ~10 dias
    const r = await executar(db, { agora: depois, chaveOpenAQ: 'k', f: fakeFetch(rotas) })
    expect(r.coletadas).toBe(0)
    expect(obs.size).toBe(0)
    expect(r.rejeitadas.filter((x) => x.motivo.startsWith('leitura antiga'))).not.toHaveLength(0)
  })

  it('nenhuma fonte responde: run termina como failed', async () => {
    const { db, runs } = bancoFalso()
    const r = await executar(db, { agora: AGORA, chaveOpenAQ: 'k', f: fakeFetch({}) })
    expect(r.status).toBe('failed')
    expect(runs[0]).toMatchObject({ status: 'failed', errorCode: 'sem_dados' })
  })
})
