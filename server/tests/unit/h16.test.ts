import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { channelTable, compositeSignal, computeHn, decodeFft, isInHn, roundHalfEven } from '../../src/protocol/h16'

// Fixtures geradas a partir do núcleo Python (hpg_core) por tests/fixtures/gerar_fixtures_h16.py.
const py = JSON.parse(readFileSync(join(__dirname, '../fixtures/h16-python.json'), 'utf8'))
const TOL = 1e-6

describe('equivalência com o núcleo Python', () => {
  it('H16 tem 159 razões, iguais e na mesma ordem do compute_hn', () => {
    const ts = computeHn(16).map(({ a, b }) => ({ a, b }))
    expect(ts).toHaveLength(159)
    expect(ts).toEqual(py.hn16)
  })

  it('tabela HPM 1.0 idêntica', () => {
    const ts = channelTable()
    expect(ts).toHaveLength(12)
    ts.forEach((ch, i) => {
      const p = py.canais[i]
      expect([ch.id, ch.label, ch.a, ch.b, ch.ratio]).toEqual([p.id, p.label, p.a, p.b, p.ratio])
      expect(ch.frequency_hz).toBeCloseTo(p.frequency_hz, 6)
      expect(ch.priority).toBeCloseTo(p.priority, 6)
    })
  })

  for (const caso of py.casos) {
    it(`sinal composto e decode_fft: ${caso.nome}`, () => {
      const sinal = compositeSignal(caso.f0, caso.harmonics, caso.duration, caso.sample_rate)
      expect(sinal.length).toBe(caso.n)
      caso.sinal_inicio.forEach((v: number, i: number) => expect(Math.abs(sinal[i] - v)).toBeLessThan(TOL))

      const picos = decodeFft(sinal, caso.sample_rate, caso.f0)
      expect(picos.map((p) => p.closest_ratio)).toEqual(caso.picos.map((p: { closest_ratio: string }) => p.closest_ratio))
      picos.forEach((p, i) => {
        const e = caso.picos[i]
        expect(p.frequency).toBeCloseTo(e.frequency, 6)
        expect(Math.abs(p.amplitude_db - e.amplitude_db)).toBeLessThan(1e-6)
        expect(Math.abs(p.deviation_hz - e.deviation_hz)).toBeLessThan(1e-6)
      })
    })
  }
})

describe('regras do protocolo', () => {
  it('pertinência a H16', () => {
    expect(isInHn(3, 2)).toBe(true)
    expect(isInHn(4, 2)).toBe(false) // não reduzida
    expect(isInHn(17, 1)).toBe(false) // fora do limite
    expect(isInHn(0, 1)).toBe(false)
    expect(isInHn(1.5, 1)).toBe(false)
  })

  it('round() do Python arredonda meio para o par', () => {
    expect([0.5, 1.5, 2.5, -0.5, 2.4, 2.6].map(roundHalfEven)).toEqual([0, 2, 2, -0, 2, 3])
  })
})
