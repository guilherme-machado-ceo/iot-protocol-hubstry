// Adaptador OpenAQ v3. Fail-closed: a estação só entra se for fixa, monitor de
// referência e se TODAS as licenças vigentes permitirem uso comercial e
// redistribuição. Coordenadas e nomes de contribuidores não são lidos.
import { z } from 'zod'
import { OPENAQ_BASE, SERIES_OPENAQ, TIMEOUT_MS } from './config'
import type { Fetch, Observacao, ResultadoFonte } from './tipos'

const Licenca = z.object({
  id: z.number(), name: z.string(),
  commercialUseAllowed: z.boolean(), redistributionAllowed: z.boolean(),
  attributionRequired: z.boolean(), sourceUrl: z.string().nullable(),
})
const Local = z.object({
  id: z.number(), locality: z.string().nullable().optional(),
  isMobile: z.boolean(), isMonitor: z.boolean(),
  provider: z.object({ name: z.string() }), owner: z.object({ name: z.string() }),
  sensors: z.array(z.object({ id: z.number(), parameter: z.object({ name: z.string(), units: z.string() }) })).max(200),
  licenses: z.array(z.object({ id: z.number(), dateTo: z.string().nullable() })).max(50).nullable().optional(),
})
const Ultima = z.object({
  value: z.number(), sensorsId: z.number(),
  datetime: z.object({ utc: z.string() }),
})

async function getJson(f: Fetch, chave: string, caminho: string): Promise<unknown> {
  const r = await f(`${OPENAQ_BASE}${caminho}`, {
    headers: { 'X-API-Key': chave, Accept: 'application/json', 'User-Agent': 'nautam-live/1.0 (Hubstry)' },
    signal: AbortSignal.timeout(TIMEOUT_MS),
  })
  if (!r.ok) throw new Error(`OpenAQ ${caminho}: HTTP ${r.status}`)
  return r.json()
}

export async function coletarOpenAQ(chave: string, f: Fetch = fetch, series = SERIES_OPENAQ): Promise<ResultadoFonte> {
  const out: ResultadoFonte = { fonte: 'openaq', observacoes: [], rejeitadas: [] }
  const licencas = new Map<number, z.infer<typeof Licenca>>()
  const locais = [...new Set(series.map((s) => s.location))]

  for (const id of locais) {
    const ref = `openaq:location:${id}`
    try {
      const local = Local.parse((await getJson(f, chave, `/locations/${id}`) as { results: unknown[] }).results[0])
      if (local.isMobile || !local.isMonitor) { out.rejeitadas.push({ ref, motivo: 'móvel ou não é monitor' }); continue }
      const vigentes = (local.licenses ?? []).filter((l) => l.dateTo === null)
      if (!vigentes.length) { out.rejeitadas.push({ ref, motivo: 'sem licença vigente' }); continue }
      const ls = []
      for (const l of vigentes) {
        if (!licencas.has(l.id)) {
          licencas.set(l.id, Licenca.parse((await getJson(f, chave, `/licenses/${l.id}`) as { results: unknown[] }).results[0]))
        }
        ls.push(licencas.get(l.id)!)
      }
      if (!ls.every((l) => l.commercialUseAllowed && l.redistributionAllowed)) {
        out.rejeitadas.push({ ref, motivo: 'licença sem uso comercial ou redistribuição' }); continue
      }
      const ultimas = z.array(Ultima).max(500).parse((await getJson(f, chave, `/locations/${id}/latest`) as { results: unknown[] }).results)
      for (const s of series.filter((x) => x.location === id)) {
        const sensor = local.sensors.find((x) => x.parameter.name === s.parameter)
        const leitura = sensor && ultimas.find((u) => u.sensorsId === sensor.id)
        if (!sensor || !leitura || !Number.isFinite(leitura.value)) {
          out.rejeitadas.push({ ref: `${ref}:${s.parameter}`, motivo: 'sem leitura do parâmetro' }); continue
        }
        const observedAt = new Date(leitura.datetime.utc)
        if (Number.isNaN(observedAt.getTime()) || observedAt.getTime() > Date.now() + 5 * 60_000) {
          out.rejeitadas.push({ ref: `${ref}:${s.parameter}`, motivo: 'instante inválido ou futuro' }); continue
        }
        const o: Observacao = {
          provider: 'openaq', stationRef: String(id), sensorRef: `openaq:sensor:${sensor.id}`,
          parameter: s.parameter, value: leitura.value, unit: sensor.parameter.units, observedAt,
          locality: local.locality ?? null,
          licenseName: ls.map((l) => l.name).join(' + '),
          licenseUrl: ls.map((l) => l.sourceUrl ?? '').filter(Boolean).join(' '),
          attribution: `${local.provider.name} via OpenAQ`,
          sourceUrl: `https://explore.openaq.org/locations/${id}`,
        }
        out.observacoes.push(o)
      }
    } catch (err) {
      out.rejeitadas.push({ ref, motivo: err instanceof Error ? err.message : String(err) })
    }
  }
  return out
}
