// Nautam Live — E2: leituras reais transmitidas por simulação de sinal HPM 1.0.
// Cada leitura vira a amplitude de um canal; o quadro recebe ruído gaussiano
// (AWGN) com semente registrada e é decodificado de duas formas:
//  - receptor HPM: conhece a tabela de 12 canais e lê só esses bins da FFT;
//  - decodificador cego: o decodeFft do núcleo, que vasculha o espectro todo.
// Nada aqui mede rádio, alcance ou energia: é simulação com dados reais.
import { channelTable, compositeSignal, decodeFft, HPM10_F0, rfftMagnitudes } from '../protocol/h16'
import { SERIES_ONS, SERIES_OPENAQ } from './config'
import type { Observacao } from './tipos'

export const QUADRO = { f0: HPM10_F0, sampleRate: 131072, duration: 1 / 64, n: 2048, thresholdDb: -40 } as const
export const DF = QUADRO.sampleRate / QUADRO.n // 64 Hz por bin
export const SNR_OPERACIONAL_DB = 20
export const LIMIAR_PRESENCA = 0.05 // metade do piso de amplitude (0,10)
const CANAIS = channelTable(QUADRO.f0)

// Faixas declaradas por parâmetro e unidade. Fora delas, satura e marca clipped.
export const FAIXAS: Record<string, { unidade: string; min: number; max: number }> = {
  pm25: { unidade: 'µg/m³', min: 0, max: 250 },
  pm10: { unidade: 'µg/m³', min: 0, max: 430 },
  o3: { unidade: 'ppm', min: 0, max: 0.2 },
  no2: { unidade: 'ppm', min: 0, max: 0.4 },
  carga: { unidade: 'MWmed', min: 0, max: 110000 },
  geracao_hidraulica: { unidade: 'MWmed', min: 0, max: 80000 },
  geracao_eolica: { unidade: 'MWmed', min: 0, max: 30000 },
  geracao_solar: { unidade: 'MWmed', min: 0, max: 30000 },
}

// Mapa fixo série -> canal, na ordem da configuração: um sensor ausente não desloca os outros.
export const CHAVES_SERIES: string[] = [
  ...SERIES_OPENAQ.map((s) => `openaq:${s.location}:${s.parameter}`),
  ...SERIES_ONS.map((s) => `ons:${s.subsistema}:${s.parameter}`),
]
export function chaveDe(o: Observacao): string {
  return `${o.provider}:${o.stationRef}:${o.parameter}`
}

export function normalizar(valor: number, parametro: string, unidade: string) {
  const f = FAIXAS[parametro]
  if (!f || f.unidade !== unidade || !Number.isFinite(valor)) return null
  const x = (valor - f.min) / (f.max - f.min)
  const clipped = x < 0 || x > 1
  return { amplitude: 0.1 + 0.9 * Math.min(1, Math.max(0, x)), clipped }
}
export function desnormalizar(amplitude: number, parametro: string): number {
  const f = FAIXAS[parametro]
  return f.min + ((amplitude - 0.1) / 0.9) * (f.max - f.min)
}

// PRNG determinístico (mulberry32) e normal padrão (Box-Muller).
export function prng(semente: number) {
  let s = semente >>> 0
  const u = () => { s = (s + 0x6d2b79f5) | 0; let t = Math.imul(s ^ (s >>> 15), 1 | s); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296 }
  return { u, normal: () => Math.sqrt(-2 * Math.log(1 - u())) * Math.cos(2 * Math.PI * u()) }
}
export function sementeDe(texto: string): number {
  let h = 2166136261
  for (const c of texto) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619) }
  return h >>> 0
}

const binDe = (f: number) => Math.round(f / DF)
// Ganho de cada canal: magnitude no bin para amplitude 1, isolado (calibração).
const GANHO = CANAIS.map((c) =>
  rfftMagnitudes(compositeSignal(QUADRO.f0, [{ a: c.a, b: c.b, amplitude: 1 }], QUADRO.duration, QUADRO.sampleRate))[binDe(c.frequency_hz)])

// amplitudes[i] = amplitude do canal i+1, ou null se ausente.
export function transmitir(amplitudes: (number | null)[], snrDb: number, semente: number) {
  const harm = CANAIS.flatMap((c, i) => (amplitudes[i] == null ? [] : [{ a: c.a, b: c.b, amplitude: amplitudes[i]! }]))
  const s = compositeSignal(QUADRO.f0, harm, QUADRO.duration, QUADRO.sampleRate)
  const ps = s.reduce((a, v) => a + v * v, 0) / s.length
  const sigma = Math.sqrt(ps / 10 ** (snrDb / 10))
  const g = prng(semente)
  let pn = 0
  const y = s.map((v) => { const n = sigma * g.normal(); pn += n * n; return v + n })
  return { y, snrMedidoDb: ps > 0 && pn > 0 ? 10 * Math.log10(ps / (pn / s.length)) : null }
}

export function receptorHpm(y: Float64Array) {
  const mags = rfftMagnitudes(y)
  return CANAIS.map((c, i) => {
    const amp = mags[binDe(c.frequency_hz)] / GANHO[i]
    return { canal: c.id, razao: c.ratio, amplitude: amp, presente: amp >= LIMIAR_PRESENCA }
  })
}

export function decodificadorCego(y: Float64Array) {
  const picos = decodeFft(y, QUADRO.sampleRate, QUADRO.f0, QUADRO.thresholdDb)
  const usados = new Set<number>()
  const achados = CANAIS.map((c) => {
    const k = picos.findIndex((p, j) => !usados.has(j) && p.ratio_a === c.a && p.ratio_b === c.b && Math.abs(p.frequency - c.frequency_hz) <= DF / 2)
    if (k >= 0) usados.add(k)
    return k >= 0
  })
  return { achados, picosTotais: picos.length, falsos: picos.length - usados.size }
}

function contar(esperado: (number | null)[], presente: boolean[], falsosExtras = 0) {
  let tp = 0, fp = falsosExtras, fn = 0
  esperado.forEach((a, i) => { if (a != null && presente[i]) tp++; else if (a != null) fn++; else if (presente[i]) fp++ })
  return { tp, fp, fn }
}
const taxa = (a: number, b: number) => (a + b > 0 ? a / (a + b) : null)

// Varredura de SNR: 20 quadros por SNR, amplitudes e presença sorteadas (p = 0,75).
export const SNRS_VARREDURA = [30, 20, 15, 10, 5, 0, -5]
export function varredura(semente: number, repeticoes = 20) {
  const g = prng(semente)
  const linhas = SNRS_VARREDURA.map((snr) => {
    const h = { tp: 0, fp: 0, fn: 0 }, c = { tp: 0, fp: 0, fn: 0 }
    let somaErro = 0, nErro = 0
    for (let r = 0; r < repeticoes; r++) {
      const amps: (number | null)[] = CANAIS.map(() => (g.u() < 0.75 ? 0.1 + 0.9 * g.u() : null))
      if (!amps.some((a) => a != null)) amps[0] = 0.5
      const { y } = transmitir(amps, snr, Math.floor(g.u() * 2 ** 32))
      const rx = receptorHpm(y)
      const ch = contar(amps, rx.map((x) => x.presente)); h.tp += ch.tp; h.fp += ch.fp; h.fn += ch.fn
      rx.forEach((x, i) => { if (amps[i] != null && x.presente) { somaErro += Math.abs(x.amplitude - amps[i]!); nErro++ } })
      const cego = decodificadorCego(y)
      const cc = contar(amps, cego.achados, cego.falsos); c.tp += cc.tp; c.fp += cc.fp; c.fn += cc.fn
    }
    return {
      snrDb: snr,
      receptorHpm: { recall: taxa(h.tp, h.fn), precisao: taxa(h.tp, h.fp), maeAmplitude: nErro ? somaErro / nErro : null },
      decodificadorCego: { recall: taxa(c.tp, c.fn), precisao: taxa(c.tp, c.fp), falsosPorQuadro: c.fp / repeticoes },
    }
  })
  const ok = (x: { recall: number | null; precisao: number | null }) => (x.recall ?? 0) >= 0.95 && (x.precisao ?? 0) >= 0.99
  const menor = (k: 'receptorHpm' | 'decodificadorCego') =>
    linhas.filter((l) => ok(l[k])).reduce<number | null>((m, l) => (m == null || l.snrDb < m ? l.snrDb : m), null)
  return { repeticoesPorSnr: repeticoes, criterio: 'recall >= 95% e precisão >= 99%', linhas,
    menorSnrTestadaDb: { receptorHpm: menor('receptorHpm'), decodificadorCego: menor('decodificadorCego') } }
}

// Os três pares de canais HPM mais próximos em frequência, testados isolados a 20 dB.
export function vizinhos(semente: number, repeticoes = 20) {
  const pares: [number, number][] = []
  for (let i = 0; i < CANAIS.length; i++) for (let j = i + 1; j < CANAIS.length; j++) pares.push([i, j])
  pares.sort((p, q) => Math.abs(CANAIS[p[0]].frequency_hz - CANAIS[p[1]].frequency_hz) - Math.abs(CANAIS[q[0]].frequency_hz - CANAIS[q[1]].frequency_hz))
  const g = prng(semente)
  return pares.slice(0, 3).map(([i, j]) => {
    let certos = 0
    for (let r = 0; r < repeticoes; r++) {
      const amps: (number | null)[] = CANAIS.map(() => null); amps[i] = 0.1 + 0.9 * g.u(); amps[j] = 0.1 + 0.9 * g.u()
      const rx = receptorHpm(transmitir(amps, SNR_OPERACIONAL_DB, Math.floor(g.u() * 2 ** 32)).y)
      certos += (rx[i].presente ? 1 : 0) + (rx[j].presente ? 1 : 0)
    }
    const sep = Math.abs(CANAIS[i].frequency_hz - CANAIS[j].frequency_hz)
    return { par: `${CANAIS[i].ratio} × ${CANAIS[j].ratio}`, separacaoHz: sep, separacaoBins: sep / DF, recall: certos / (2 * repeticoes) }
  })
}

// Linha de base MQTT 3.1.1 (cálculo, sem broker): mesma carga lógica em JSON canônico.
export function remainingLengthBytes(n: number): number {
  let b = 0
  do { b++; n = Math.floor(n / 128) } while (n > 0)
  return b
}
export function baselineMqtt(leituras: { chave: string; valor: number; unidade: string; instante: string }[], topico = 'nautam/live/readings') {
  const payload = Buffer.byteLength(JSON.stringify([...leituras].sort((a, b) => a.chave.localeCompare(b.chave))), 'utf8')
  const t = Buffer.byteLength(topico, 'utf8')
  const total = (vh: number) => { const rem = vh + payload; return 1 + remainingLengthBytes(rem) + rem }
  const q0 = total(2 + t), q1 = total(2 + t + 2)
  return { topico, payloadBytes: payload, publishQos0Bytes: q0, overheadQos0Bytes: q0 - payload,
    trocaQos1Bytes: q1 + 4, overheadQos1Bytes: q1 + 4 - payload,
    vetorAmostrasFloat64Bytes: QUADRO.n * 8,
    exclui: 'TCP/IP, TLS, rádio, keepalive, retransmissões, sessão do broker e energia' }
}

// Execução do protocolo sobre as leituras de um slot.
export function executarProtocolo(obs: Observacao[], slotIso: string) {
  const porChave = new Map(obs.map((o) => [chaveDe(o), o]))
  const excluidas: { chave: string; motivo: string }[] = []
  const canais = CHAVES_SERIES.slice(0, CANAIS.length).map((chave, i) => {
    const o = porChave.get(chave)
    const n = o ? normalizar(o.value, o.parameter, o.unit) : null
    if (o && !n) excluidas.push({ chave, motivo: `faixa/unidade não declarada (${o.parameter} ${o.unit})` })
    return { canal: CANAIS[i].id, razao: CANAIS[i].ratio, chave, observacao: o ?? null, amplitude: n?.amplitude ?? null, clipped: n?.clipped ?? false }
  })
  const semente = sementeDe(slotIso)
  const t0 = performance.now()
  const { y, snrMedidoDb } = transmitir(canais.map((c) => c.amplitude), SNR_OPERACIONAL_DB, semente)
  const rx = receptorHpm(y)
  const cego = decodificadorCego(y)
  const tempoMs = performance.now() - t0
  const conta = contar(canais.map((c) => c.amplitude), rx.map((x) => x.presente))
  const recuperados = canais.map((c, i) => {
    const o = c.observacao
    const valorRecuperado = rx[i].presente && o ? desnormalizar(rx[i].amplitude, o.parameter) : null
    return { canal: c.canal, razao: c.razao, chave: c.chave, parametro: o?.parameter ?? null, unidade: o?.unit ?? null,
      valorOriginal: o?.value ?? null, amplitudeEnviada: c.amplitude, amplitudeRecebida: rx[i].amplitude, presente: rx[i].presente,
      valorRecuperado, erroAbsoluto: valorRecuperado != null && o ? Math.abs(valorRecuperado - o.value) : null, clipped: c.clipped }
  })
  const comErro = recuperados.filter((r) => r.erroAbsoluto != null && r.amplitudeEnviada != null)
  const leiturasMqtt = canais.filter((c) => c.observacao).map((c) => ({ chave: c.chave, valor: c.observacao!.value, unidade: c.observacao!.unit, instante: c.observacao!.observedAt.toISOString() }))
  return {
    noiseSeed: String(semente),
    requestedSnrDb: SNR_OPERACIONAL_DB,
    measuredSnrDb: snrMedidoDb,
    expectedChannels: canais.map((c) => ({ canal: c.canal, razao: c.razao, chave: c.chave, amplitude: c.amplitude, clipped: c.clipped })),
    decodedPeaks: { receptorHpm: recuperados, decodificadorCego: { canaisAchados: cego.achados.filter(Boolean).length, picosTotais: cego.picosTotais, falsos: cego.falsos } },
    metrics: {
      quadro: { ...QUADRO, resolucaoHz: DF, valoresPorQuadro: canais.filter((c) => c.amplitude != null).length, valoresPorSegundoSimulado: canais.filter((c) => c.amplitude != null).length / QUADRO.duration },
      execucao: { ...conta, recall: taxa(conta.tp, conta.fn), precisao: taxa(conta.tp, conta.fp),
        maeAmplitude: comErro.length ? comErro.reduce((a, r) => a + Math.abs(r.amplitudeRecebida - r.amplitudeEnviada!), 0) / comErro.length : null,
        tempoMs },
      varredura: varredura(semente ^ 0x9e3779b9),
      vizinhos: vizinhos(semente ^ 0x85ebca6b),
      excluidas,
      declaracao: 'simulação de sinal com dados reais; energia e interferência em campo não medidas',
    },
    mqttBaseline: baselineMqtt(leiturasMqtt),
  }
}
