import { describe, expect, it } from 'vitest'
import { baselineMqtt, BINS, CHAVES_SERIES, desnormalizar, executarProtocolo, FASES, goertzel, normalizar, QUADRO, quadroPcm, receptorHpm, remainingLengthBytes, transmitir, varredura, vizinhos } from '../../src/live/protocolo'
import { channelTable, compositeSignal, rfftMagnitudes } from '../../src/protocol/h16'
import type { Observacao } from '../../src/live/tipos'

const base = { licenseName: 'x', licenseUrl: 'x', attribution: 'x', sourceUrl: 'x', locality: null, observedAt: new Date('2026-11-03T13:00:00Z') }
const obs: Observacao[] = [
  { ...base, provider: 'openaq', stationRef: '162', sensorRef: 's1', parameter: 'pm25', value: 12.5, unit: 'µg/m³' },
  { ...base, provider: 'openaq', stationRef: '162', sensorRef: 's2', parameter: 'o3', value: 0.031, unit: 'ppm' },
  { ...base, provider: 'ons', stationRef: 'SIN', sensorRef: 'ons:SIN:val_carga', parameter: 'carga', value: 74019.45, unit: 'MWmed' },
  { ...base, provider: 'ons', stationRef: 'SIN', sensorRef: 'ons:SIN:val_gersolar', parameter: 'geracao_solar', value: 0, unit: 'MWmed' },
]

describe('normalização', () => {
  it('piso de 0,10, saturação marcada e ida e volta exata', () => {
    expect(normalizar(0, 'pm25', 'µg/m³')).toEqual({ amplitude: 0.1, clipped: false })
    expect(normalizar(999, 'pm25', 'µg/m³')).toEqual({ amplitude: 1, clipped: true })
    expect(normalizar(1, 'pm25', 'ppm')).toBeNull() // unidade errada não entra
    const n = normalizar(74019.45, 'carga', 'MWmed')!
    expect(desnormalizar(n.amplitude, 'carga')).toBeCloseTo(74019.45, 6)
    // ruído abaixo do piso ou acima do teto não gera valor fora da faixa
    expect(desnormalizar(0.09, 'geracao_solar')).toBe(0)
    expect(desnormalizar(1.05, 'pm25')).toBe(250)
  })
})

describe('transmissão e recepção', () => {
  it('mesma semente, mesmo quadro; semente diferente, ruído diferente', () => {
    const a = transmitir([0.5, 0.3, null, 0.9, null, null, null, null, null, null, null, null], 20, 42)
    const b = transmitir([0.5, 0.3, null, 0.9, null, null, null, null, null, null, null, null], 20, 42)
    const c = transmitir([0.5, 0.3, null, 0.9, null, null, null, null, null, null, null, null], 20, 43)
    expect(Array.from(a.y)).toEqual(Array.from(b.y))
    expect(Array.from(a.y)).not.toEqual(Array.from(c.y))
    expect(a.y.length).toBe(QUADRO.n)
    expect(a.snrMedidoDb!).toBeGreaterThan(19); expect(a.snrMedidoDb!).toBeLessThan(21)
  })

  it('sem ruído, o receptor HPM recupera as amplitudes (só erro de quantização PCM) e não inventa canal', () => {
    const amps = [0.5, 0.3, null, 0.9, null, 0.1, null, null, 1, null, null, 0.7]
    const rx = receptorHpm(transmitir(amps, 300, 1).y)
    rx.forEach((x, i) => {
      expect(x.presente).toBe(amps[i] != null)
      expect(Math.abs(x.amplitude - (amps[i] ?? 0))).toBeLessThan(1e-3)
    })
  })
})

describe('perfil HPM-D48 coerente', () => {
  it('48 kHz, 480 amostras, f0 6 kHz, 100 Hz por bin; os 12 canais em bins inteiros abaixo de Nyquist', () => {
    expect(QUADRO).toMatchObject({ sampleRate: 48000, n: 480, f0: 6000 })
    expect(BINS.every((k) => Number.isInteger(k))).toBe(true)
    expect(Math.max(...BINS)).toBeLessThan(QUADRO.n / 2)
  })

  it('tons ortogonais: correlação cruzada máxima entre os 12 canais < 1e-10', () => {
    const tons = channelTable(QUADRO.f0).map((c, i) => compositeSignal(QUADRO.f0, [{ a: c.a, b: c.b, phase: FASES[i] }], QUADRO.duration, QUADRO.sampleRate))
    const dot = (a: Float64Array, b: Float64Array) => a.reduce((s, v, i) => s + v * b[i], 0)
    let max = 0
    for (let i = 0; i < tons.length; i++) for (let j = i + 1; j < tons.length; j++)
      max = Math.max(max, Math.abs(dot(tons[i], tons[j])) / Math.sqrt(dot(tons[i], tons[i]) * dot(tons[j], tons[j])))
    expect(max).toBeLessThan(1e-10)
  })

  it('Goertzel coincide com a DFT completa nos bins dos canais', () => {
    const y = transmitir([0.5, 0.3, null, 0.9, null, 0.1, null, null, 1, null, null, 0.7], 20, 3).y
    const mags = rfftMagnitudes(y)
    BINS.forEach((k) => expect(goertzel(y, k)).toBeCloseTo(mags[k], 8))
  })

  it('PCM de 16 bits sem clipping mesmo com os 12 canais no máximo; fator de crista medido', () => {
    const q = quadroPcm(Array(12).fill(1))
    expect(q.clipping).toBe(0)
    expect(q.picoDbfs!).toBeLessThanOrEqual(-1)
    expect(q.fatorCristaDb!).toBeGreaterThan(0)
    expect(q.pcm).toBeInstanceOf(Int16Array)
  })
})

describe('execução sobre leituras reais', () => {
  const r = executarProtocolo(obs, '2026-11-03T13:35:00.000Z')

  it('mapa de canais é fixo: sensor ausente não desloca os demais', () => {
    const chaves = r.expectedChannels.map((c) => c.chave)
    expect(chaves).toEqual(CHAVES_SERIES.slice(0, 12))
    const carga = r.expectedChannels.find((c) => c.chave === 'ons:SIN:carga')!
    expect(carga.canal).toBe(9) // 8 séries de ar antes, mesmo com só 2 presentes
    expect(r.expectedChannels.filter((c) => c.amplitude != null)).toHaveLength(4)
  })

  it('recupera os valores reais com erro pequeno a 20 dB e registra a semente', () => {
    const rec = r.decodedPeaks.receptorHpm.filter((x) => x.valorOriginal != null)
    expect(rec).toHaveLength(4)
    for (const x of rec) {
      expect(x.presente).toBe(true)
      expect(Math.abs(x.amplitudeRecebida - x.amplitudeEnviada!)).toBeLessThan(0.05)
    }
    expect(r.metrics.quadro).toMatchObject({ perfil: 'HPM-D48', binsInteiros: true, clippingTx: 0 })
    expect(r.metrics.execucao.recall).toBe(1)
    expect(r.noiseSeed).toMatch(/^\d+$/)
    expect(r.metrics.declaracao).toContain('simulação de sinal com dados reais')
    // determinístico por slot
    expect(executarProtocolo(obs, '2026-11-03T13:35:00.000Z').decodedPeaks).toEqual(r.decodedPeaks)
  })
})

describe('varredura, vizinhos e MQTT', () => {
  it('varredura: 7 SNRs, 20 repetições, os dois receptores medidos', () => {
    const v = varredura(1)
    expect(v.linhas.map((l) => l.snrDb)).toEqual([30, 20, 15, 10, 5, 0, -5])
    expect(v.repeticoesPorSnr).toBe(20)
    expect(v.linhas[0].receptorHpm.recall).toBe(1)
    // O receptor HPM atende o critério até 15 dB; o decodificador cego
    // (decodeFft, limiar -40 dB) não atende em nenhuma SNR testada.
    expect(v.menorSnrTestadaDb.receptorHpm).not.toBeNull()
    expect(v.menorSnrTestadaDb.decodificadorCego).toBeNull()
    expect(varredura(1)).toEqual(v)
  })

  it('três pares vizinhos com separação em Hz e bins', () => {
    const p = vizinhos(1)
    expect(p).toHaveLength(3)
    expect(p[0].separacaoHz).toBeLessThanOrEqual(p[1].separacaoHz)
    expect(p[0].separacaoBins).toBeCloseTo(p[0].separacaoHz / 100, 9)
  })

  it('Remaining Length do MQTT nas fronteiras 127/128 e 16383/16384', () => {
    expect([127, 128, 16383, 16384].map(remainingLengthBytes)).toEqual([1, 2, 2, 3])
  })

  it('QoS 1 acrescenta Packet Identifier (2) e PUBACK (4)', () => {
    const m = baselineMqtt([{ chave: 'a', valor: 1, unidade: 'u', instante: 't' }])
    expect(m.trocaQos1Bytes - m.publishQos0Bytes).toBe(6)
    expect(m.quadroPcmBytes).toBe(480 * 2)
  })
})
