// Painel público do Nautam Live (E3).
//   GET /live                      -> página do painel (HTML, JS e CSS em arquivos separados, por causa da CSP do helmet)
//   GET /live/:arquivo             -> app.js, app.css
//   GET /live/assets/:arquivo      -> logo, favicon e selo
//   GET /api/live/public           -> resumo público: última execução, leituras com licença e série histórica
//
// O endpoint público não expõe coordenadas, segredos, corpo bruto das fontes nem stack trace.
import { readFileSync, existsSync } from 'node:fs'
import { join } from 'node:path'
import type { FastifyInstance } from 'fastify'
import { prisma } from '../db'
import { CHAVES_SERIES } from '../live/protocolo'
import { IDADE_MAXIMA_H, idadeHoras } from '../live/config'

export const DECLARACAO = 'simulação de sinal com dados reais; energia e interferência em campo não medidas'
export const MINUTOS_DESATUALIZADO = 15
export const MAX_PONTOS = 1000
const CACHE_MS = 60_000

const JANELAS: Record<string, { horas: number; bucket: 'hour' | 'raw' }> = {
  '24h': { horas: 24, bucket: 'raw' },
  '7d': { horas: 24 * 7, bucket: 'hour' },
  '30d': { horas: 24 * 30, bucket: 'hour' },
}

// Natureza de cada família de série, exibida ao lado do valor (Req. 11.5).
const NATUREZA: Record<string, string> = {
  openaq: 'medição física de monitor oficial (AirNow, EUA), valor horário; pode ser revisado pela agência',
  ons: 'valor operacional consolidado pelo ONS, média horária; publicado com 1 a 2 dias de defasagem',
}

const TIPOS: Record<string, string> = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
}

function carregarEstaticos(raiz: string) {
  const mapa = new Map<string, { corpo: Buffer; tipo: string }>()
  const arquivos = ['index.html', 'app.js', 'app.css',
    'assets/hubstry-logo-claro.png', 'assets/favicon-32.png', 'assets/favicon-180.png', 'assets/nvidia-inception.svg']
  for (const a of arquivos) {
    const p = join(raiz, a)
    if (existsSync(p)) mapa.set(a, { corpo: readFileSync(p), tipo: TIPOS[a.slice(a.lastIndexOf('.'))] })
  }
  return mapa
}

export function parseChave(chave: string) {
  if (!CHAVES_SERIES.includes(chave)) return null
  const [provider, stationRef, parameter] = chave.split(':')
  return { provider, stationRef, parameter }
}

type Ponto = { t: Date; v: number }

async function serie(chave: string, janela: string): Promise<Ponto[]> {
  const s = parseChave(chave)!
  const { horas, bucket } = JANELAS[janela]
  const desde = new Date(Date.now() - horas * 3600_000)
  const linhas: Ponto[] = bucket === 'raw'
    ? await prisma.$queryRaw<Ponto[]>`
        SELECT "observedAt" AS t, "value" AS v FROM "LiveObservation"
        WHERE provider = ${s.provider} AND "stationRef" = ${s.stationRef} AND parameter = ${s.parameter} AND "observedAt" >= ${desde}
        ORDER BY "observedAt" LIMIT ${MAX_PONTOS}`
    : await prisma.$queryRaw<Ponto[]>`
        SELECT date_trunc('hour', "observedAt") AS t, avg("value")::float8 AS v FROM "LiveObservation"
        WHERE provider = ${s.provider} AND "stationRef" = ${s.stationRef} AND parameter = ${s.parameter} AND "observedAt" >= ${desde}
        GROUP BY 1 ORDER BY 1 LIMIT ${MAX_PONTOS}`
  return linhas.map((l) => ({ t: new Date(l.t), v: Number(l.v) }))
}

async function resumo() {
  const ultimaOk = await prisma.liveRun.findFirst({
    where: { status: { in: ['succeeded', 'no_new_data'] } },
    orderBy: { slotUtc: 'desc' },
  })
  const ultima = await prisma.liveRun.findFirst({ orderBy: { slotUtc: 'desc' } })
  const comProtocolo = await prisma.liveRun.findFirst({ where: { measuredSnrDb: { not: null } }, orderBy: { slotUtc: 'desc' } })
  const recentes = await prisma.liveRun.findMany({ orderBy: { slotUtc: 'desc' }, take: 12,
    select: { slotUtc: true, status: true, newObservations: true, measuredSnrDb: true } })

  // Última leitura de cada série configurada, com proveniência e licença.
  const leituras = (await Promise.all(CHAVES_SERIES.map(async (chave) => {
    const s = parseChave(chave)!
    const o = await prisma.liveObservation.findFirst({
      where: { provider: s.provider, stationRef: s.stationRef, parameter: s.parameter },
      orderBy: { observedAt: 'desc' },
      select: { provider: true, stationRef: true, parameter: true, value: true, unit: true, observedAt: true, ingestedAt: true,
        locality: true, licenseName: true, licenseUrl: true, attribution: true, sourceUrl: true },
    })
    if (!o) return null
    const idade = idadeHoras(o.observedAt, new Date())
    // Leitura antiga demais não aparece como atual no painel.
    if (idade > IDADE_MAXIMA_H[o.provider as 'openaq' | 'ons']) return null
    return { chave, ...o, idadeHoras: Math.round(idade * 10) / 10, natureza: NATUREZA[o.provider] }
  }))).filter(Boolean)

  const referencia = ultimaOk?.completedAt ?? null
  const desatualizado = !referencia || Date.now() - referencia.getTime() > MINUTOS_DESATUALIZADO * 60_000
  const estado = !ultima ? 'sem_dados' : ultima.status === 'failed' ? 'falha' : desatualizado ? 'desatualizado' : 'normal'

  return {
    declaracao: DECLARACAO,
    geradoEm: new Date().toISOString(),
    estado,
    desatualizado,
    limiteDesatualizadoMin: MINUTOS_DESATUALIZADO,
    ultimaExecucao: ultima && { slotUtc: ultima.slotUtc, status: ultima.status, novas: ultima.newObservations, concluidaEm: ultima.completedAt },
    ultimaExecucaoOk: ultimaOk && { slotUtc: ultimaOk.slotUtc, status: ultimaOk.status, concluidaEm: ultimaOk.completedAt },
    protocolo: comProtocolo && {
      slotUtc: comProtocolo.slotUtc,
      snrSolicitadoDb: comProtocolo.requestedSnrDb,
      snrMedidoDb: comProtocolo.measuredSnrDb,
      semente: comProtocolo.noiseSeed,
      canais: comProtocolo.decodedPeaks,
      metricas: comProtocolo.metrics,
      mqtt: comProtocolo.mqttBaseline,
    },
    execucoesRecentes: recentes,
    leituras,
    series: CHAVES_SERIES,
  }
}

let cache: { em: number; corpo: Awaited<ReturnType<typeof resumo>> } | null = null
const cacheSeries = new Map<string, { em: number; pontos: Ponto[] }>()
export function limparCache() { cache = null; cacheSeries.clear() }

export async function liveRoutes(app: FastifyInstance, opts: { raiz?: string } = {}) {
  const estaticos = carregarEstaticos(opts.raiz ?? join(process.cwd(), 'public', 'live'))

  const servir = (nome: string) => async (_req: unknown, reply: import('fastify').FastifyReply) => {
    const a = estaticos.get(nome)
    if (!a) return reply.code(404).send({ message: 'não encontrado' })
    return reply.header('content-type', a.tipo).header('cache-control', nome === 'index.html' ? 'no-cache' : 'public, max-age=300').send(a.corpo)
  }

  app.get('/live', { schema: { hide: true } }, servir('index.html'))
  app.get<{ Params: { arquivo: string } }>('/live/:arquivo', { schema: { hide: true } }, (req, reply) => servir(req.params.arquivo)(req, reply))
  app.get<{ Params: { arquivo: string } }>('/live/assets/:arquivo', { schema: { hide: true } }, (req, reply) => servir(`assets/${req.params.arquivo}`)(req, reply))
  app.get('/favicon.ico', { schema: { hide: true } }, servir('assets/favicon-32.png'))

  app.get<{ Querystring: { window?: string; series?: string } }>('/api/live/public', {
    schema: {
      tags: ['live'],
      summary: 'Resumo público do Nautam Live (sem autenticação)',
      querystring: {
        type: 'object',
        properties: { window: { type: 'string', enum: Object.keys(JANELAS) }, series: { type: 'string', maxLength: 80 } },
        additionalProperties: false,
      },
    },
  }, async (req, reply) => {
    const janela = req.query.window ?? '24h'
    if (req.query.series && !parseChave(req.query.series)) return reply.code(400).send({ message: 'série desconhecida' })
    if (!cache || Date.now() - cache.em > CACHE_MS) cache = { em: Date.now(), corpo: await resumo() }
    let pontos: Ponto[] = []
    if (req.query.series) {
      const k = `${janela}|${req.query.series}`
      const c = cacheSeries.get(k)
      if (c && Date.now() - c.em <= CACHE_MS) pontos = c.pontos
      else { pontos = await serie(req.query.series, janela); cacheSeries.set(k, { em: Date.now(), pontos }) }
    }
    reply.header('cache-control', 'public, max-age=60')
    return { ...cache.corpo, janela, serie: req.query.series ?? null, pontos: pontos.slice(0, MAX_PONTOS) }
  })
}
