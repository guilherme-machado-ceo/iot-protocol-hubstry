// Núcleo do protocolo harmônico em TypeScript.
// Porte fiel de hpg_core/omnigrid.py (compute_hn), hpg_core/hpm_config.py
// (HPM 1.0) e hpg_core/signal_processing.py (sinal composto e decode_fft).
// A equivalência com o Python é verificada por fixtures geradas a partir do
// próprio núcleo Python (tests/fixtures/gerar_fixtures_h16.py).

export interface Ratio {
  a: number
  b: number
  value: number
}

export interface HarmonicSpec {
  a: number
  b: number
  amplitude?: number
  phase?: number
}

export interface Channel {
  id: number
  label: string
  a: number
  b: number
  ratio: string
  frequency_hz: number
  priority: number
}

export interface DetectedPeak {
  frequency: number
  amplitude_db: number
  ratio_a: number
  ratio_b: number
  closest_ratio: string
  deviation_hz: number
  in_h16: boolean
}

export const HPM10_F0 = 16384.0
export const H_N_MAX = 16

// Tabela de canais do HPM 1.0 (id, a, b, rótulo), idêntica a hpm_config.py.
const HPM10_DEFS: ReadonlyArray<[number, number, number, string]> = [
  [1, 1, 1, 'CH1'], [2, 2, 1, 'CH2'], [3, 3, 2, 'CH3'], [4, 4, 3, 'CH4'],
  [5, 5, 4, 'CH5'], [6, 3, 1, 'CH6'], [7, 5, 3, 'CH7'], [8, 7, 4, 'CH8'],
  [9, 7, 5, 'CH9'], [10, 8, 5, 'CH10'], [11, 5, 2, 'CH11'], [12, 7, 3, 'CH12'],
]

export function gcd(x: number, y: number): number {
  x = Math.abs(x); y = Math.abs(y)
  while (y) [x, y] = [y, x % y]
  return x
}

// H_N = { a/b : gcd(a, b) = 1, 1 ≤ a ≤ N, 1 ≤ b ≤ N }, ordenado pelo valor.
// Para N = 16, |H_16| = 159.
export function computeHn(N: number = H_N_MAX): Ratio[] {
  const out: Ratio[] = []
  for (let b = 1; b <= N; b++) {
    for (let a = 1; a <= N; a++) {
      if (gcd(a, b) === 1) out.push({ a, b, value: a / b })
    }
  }
  return out.sort((r, s) => r.value - s.value || r.b - s.b)
}

export function isInHn(a: number, b: number, N: number = H_N_MAX): boolean {
  return Number.isInteger(a) && Number.isInteger(b) && a >= 1 && b >= 1 && a <= N && b <= N && gcd(a, b) === 1
}

export function channelTable(f0: number = HPM10_F0): Channel[] {
  return HPM10_DEFS.map(([id, a, b, label]) => ({
    id, label, a, b,
    ratio: `${a}/${b}`,
    frequency_hz: (a / b) * f0,
    priority: 1.0 / (a + b),
  }))
}

export function frequencyOf(a: number, b: number, f0: number): number {
  return (a / b) * f0
}

// s(t) = Σ Aₖ sin(2π (aₖ/bₖ) f₀ t + φₖ), com t = linspace(0, duração, n, endpoint=False)
export function compositeSignal(f0: number, harmonics: HarmonicSpec[], duration: number, sampleRate: number): Float64Array {
  const n = Math.trunc(sampleRate * duration)
  const signal = new Float64Array(n)
  for (const h of harmonics) {
    const amp = h.amplitude ?? 1.0
    const phase = h.phase ?? 0.0
    const w = 2 * Math.PI * frequencyOf(h.a, h.b, f0)
    for (let i = 0; i < n; i++) {
      const t = (duration * i) / n
      signal[i] += amp * Math.sin(w * t + phase)
    }
  }
  return signal
}

// Módulo do espectro de frequências positivas (equivalente a |numpy.fft.rfft|).
// FFT radix-2 quando n é potência de 2; DFT direta nos demais casos (limitada por quem chama).
export function rfftMagnitudes(signal: Float64Array): Float64Array {
  const n = signal.length
  const half = Math.floor(n / 2) + 1
  const mags = new Float64Array(half)
  if (n > 0 && (n & (n - 1)) === 0) {
    const re = Float64Array.from(signal)
    const im = new Float64Array(n)
    for (let i = 1, j = 0; i < n; i++) {
      let bit = n >> 1
      for (; j & bit; bit >>= 1) j ^= bit
      j ^= bit
      if (i < j) { [re[i], re[j]] = [re[j], re[i]] }
    }
    for (let len = 2; len <= n; len <<= 1) {
      const ang = (-2 * Math.PI) / len
      for (let i = 0; i < n; i += len) {
        for (let k = 0; k < len / 2; k++) {
          const wr = Math.cos(ang * k), wi = Math.sin(ang * k)
          const ur = re[i + k], ui = im[i + k]
          const vr = re[i + k + len / 2] * wr - im[i + k + len / 2] * wi
          const vi = re[i + k + len / 2] * wi + im[i + k + len / 2] * wr
          re[i + k] = ur + vr; im[i + k] = ui + vi
          re[i + k + len / 2] = ur - vr; im[i + k + len / 2] = ui - vi
        }
      }
    }
    for (let k = 0; k < half; k++) mags[k] = Math.hypot(re[k], im[k])
    return mags
  }
  for (let k = 0; k < half; k++) {
    let sr = 0, si = 0
    for (let t = 0; t < n; t++) {
      const ang = (-2 * Math.PI * k * t) / n
      sr += signal[t] * Math.cos(ang)
      si += signal[t] * Math.sin(ang)
    }
    mags[k] = Math.hypot(sr, si)
  }
  return mags
}

// round() do Python: arredondamento "meio para o par".
export function roundHalfEven(x: number): number {
  const r = Math.round(x)
  return Math.abs(x % 1) === 0.5 && r % 2 !== 0 ? r - 1 : r
}

// Porte de decode_fft: picos acima do limiar e razão a/b mais próxima (b ≤ 32, a ≤ 100).
export function decodeFft(signal: Float64Array, sampleRate: number, f0: number, thresholdDb = -40.0): DetectedPeak[] {
  const n = signal.length
  const mags = rfftMagnitudes(signal)
  let maxMag = 0
  for (const m of mags) if (m > maxMag) maxMag = m
  const db = Array.from(mags, (m) => (maxMag > 0 ? 20 * Math.log10(m / maxMag + 1e-12) : -Infinity))

  const detected: DetectedPeak[] = []
  for (let i = 1; i < mags.length - 1; i++) {
    if (db[i] > thresholdDb && db[i] > db[i - 1] && db[i] > db[i + 1]) {
      const freq = (i * sampleRate) / n
      const ratio = f0 > 0 ? freq / f0 : 0
      let bestA = 1, bestB = 1, bestDev = Math.abs(ratio - 1)
      for (let b = 1; b < 33; b++) {
        const a = roundHalfEven(ratio * b)
        if (a > 0 && a <= 100) {
          const dev = Math.abs(ratio - a / b)
          if (dev < bestDev) { bestA = a; bestB = b; bestDev = dev }
        }
      }
      detected.push({
        frequency: freq,
        amplitude_db: db[i],
        ratio_a: bestA,
        ratio_b: bestB,
        closest_ratio: `${bestA}/${bestB}`,
        deviation_hz: bestDev * f0,
        in_h16: isInHn(bestA, bestB),
      })
    }
  }
  return detected.sort((p, q) => q.amplitude_db - p.amplitude_db)
}
