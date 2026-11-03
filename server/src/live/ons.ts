// Adaptador ONS: balanço de energia horário por subsistema (CC BY 4.0), lido do
// bucket público do Open Data on AWS sem assinatura. Para não baixar o arquivo
// inteiro (~4 MB), lê só os últimos bytes por HTTP Range.
import { ONS_BASE, ONS_BUCKET, ONS_PREFIXO, SERIES_ONS, TIMEOUT_MS } from './config'
import type { Fetch, Observacao, ResultadoFonte } from './tipos'

const LICENCA = { licenseName: 'CC BY 4.0', licenseUrl: 'https://creativecommons.org/licenses/by/4.0/' }
const BYTES_FINAIS = 8192

// din_instante vem no horário de Brasília (UTC-3, sem horário de verão desde 2019).
export function instanteOnsParaUtc(s: string): Date {
  const m = /^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})$/.exec(s.trim())
  if (!m) return new Date(NaN)
  return new Date(Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4] + 3, +m[5], +m[6]))
}

export function interpretarCauda(texto: string, ano: number, series = SERIES_ONS): Observacao[] {
  const cab = ['id_subsistema', 'nom_subsistema', 'din_instante', 'val_gerhidraulica', 'val_gertermica', 'val_gereolica', 'val_gersolar', 'val_carga', 'val_intercambio']
  // A primeira linha da cauda pode vir cortada; só linhas completas com 9 campos.
  const linhas = texto.split('\n').map((l) => l.replace(/\r$/, '')).filter((l) => l.split(';').length === cab.length)
  const out: Observacao[] = []
  for (const s of series) {
    const ultima = [...linhas].reverse().find((l) => l.split(';')[0].trim() === s.subsistema)
    if (!ultima) continue
    const campos = ultima.split(';')
    const valor = Number(campos[cab.indexOf(s.coluna)])
    const observedAt = instanteOnsParaUtc(campos[2])
    if (!Number.isFinite(valor) || Number.isNaN(observedAt.getTime())) continue
    out.push({
      provider: 'ons', stationRef: s.subsistema, sensorRef: `ons:${s.subsistema}:${s.coluna}`,
      parameter: s.parameter, value: valor, unit: 'MWmed', observedAt, locality: campos[1].trim(),
      ...LICENCA, attribution: 'Operador Nacional do Sistema Elétrico (ONS), Dados Abertos',
      sourceUrl: `${ONS_BASE}/BALANCO_ENERGIA_SUBSISTEMA_${ano}.csv`,
    })
  }
  return out
}

export async function coletarONS(f: Fetch = fetch, agora = new Date()): Promise<ResultadoFonte> {
  const out: ResultadoFonte = { fonte: 'ons', observacoes: [], rejeitadas: [] }
  // Na virada do ano o arquivo novo pode ainda não existir: tenta o ano anterior.
  const pedir = (url: string) => f(url, {
    headers: { Range: `bytes=-${BYTES_FINAIS}`, 'User-Agent': 'nautam-live/1.0 (Hubstry)' },
    signal: AbortSignal.timeout(TIMEOUT_MS), redirect: 'manual',
  })
  for (const ano of [agora.getUTCFullYear(), agora.getUTCFullYear() - 1]) {
    try {
      const arquivo = `BALANCO_ENERGIA_SUBSISTEMA_${ano}.csv`
      let r = await pedir(`${ONS_BASE}/${arquivo}`)
      // O S3 responde 301 (PermanentRedirect) sem Location quando o endpoint não é
      // o da região do bucket; a região certa vem no cabeçalho x-amz-bucket-region.
      const regiao = r.headers.get('x-amz-bucket-region')
      if ((r.status === 301 || r.status === 307) && regiao) {
        r = await pedir(`https://${ONS_BUCKET}.s3.${regiao}.amazonaws.com/${ONS_PREFIXO}/${arquivo}`)
      }
      if (r.status === 404 || r.status === 403) continue
      if (!r.ok) throw new Error(`ONS ${ano}: HTTP ${r.status}`)
      out.observacoes = interpretarCauda(await r.text(), ano)
      if (out.observacoes.length) return out
    } catch (err) {
      out.rejeitadas.push({ ref: `ons:${ano}`, motivo: err instanceof Error ? err.message : String(err) })
      return out
    }
  }
  out.rejeitadas.push({ ref: 'ons', motivo: 'nenhum arquivo do ano atual ou anterior com dados' })
  return out
}
