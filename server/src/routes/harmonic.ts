import type { FastifyInstance, FastifyReply } from 'fastify'
import { z } from 'zod'
import { prisma } from '../db'
import { requireScope } from '../auth'
import {
  HPM10_F0, H_N_MAX, channelTable, compositeSignal, computeHn, decodeFft, frequencyOf, isInHn,
  type HarmonicSpec,
} from '../protocol/h16'

// Contrato da API alinhado ao núcleo Python (hpg_core): razões a/b do conjunto H16
// e canais do HPM 1.0, em vez dos antigos harmônicos inteiros f0 × n.

const Harmonic = z.object({
  a: z.number().int(),
  b: z.number().int(),
  amplitude: z.number().finite().default(1.0),
  phase: z.number().finite().default(0.0),
})

const Components = z.object({
  f0: z.number().positive().max(1e7).default(HPM10_F0),
  channels: z.array(z.number().int().min(1).max(12)).min(1).max(12).optional(),
  harmonics: z.array(Harmonic).min(1).max(32).optional(),
}).refine((v) => !(v.channels && v.harmonics), { message: 'Use channels (HPM 1.0) ou harmonics (a/b), não os dois.' })

const SimulateBody = Components.and(z.object({ message: z.string().max(256).optional() }))

const FftBody = Components.and(z.object({
  sampleRate: z.number().positive().max(1e7).default(131072),
  duration: z.number().positive().max(10).default(1 / 64),
  thresholdDb: z.number().max(0).default(-40),
}))

const MAX_SAMPLES_POT2 = 65536
const MAX_SAMPLES_DFT = 4096

function badRequest(reply: FastifyReply, message: string, details?: unknown) {
  return reply.code(400).send({ error: 'bad_request', message, details })
}

// Resolve canais do HPM 1.0 ou razões explícitas; razões fora de H16 são rejeitadas.
function resolveHarmonics(input: { channels?: number[]; harmonics?: HarmonicSpec[] }): HarmonicSpec[] | string {
  if (input.harmonics) {
    const fora = input.harmonics.filter((h) => !isInHn(h.a, h.b))
    if (fora.length) return `Razões fora de H16 (a, b ≤ ${H_N_MAX}, irredutíveis): ${fora.map((h) => `${h.a}/${h.b}`).join(', ')}`
    return input.harmonics
  }
  const tabela = channelTable()
  const ids = input.channels ?? tabela.slice(0, 6).map((c) => c.id)
  return ids.map((id) => ({ a: tabela[id - 1].a, b: tabela[id - 1].b, amplitude: 1.0, phase: 0.0 }))
}

export async function harmonicRoutes(app: FastifyInstance) {
  app.get('/hn', {
    preHandler: requireScope('harmonic:compute'),
    schema: {
      tags: ['harmonic'],
      summary: 'Conjunto H_N de razões a/b irredutíveis (padrão N = 16)',
      querystring: { type: 'object', properties: { N: { type: 'integer', minimum: 1, maximum: 32, default: 16 } } },
    },
  }, async (req, reply) => {
    const { N = 16 } = req.query as { N?: number }
    const ratios = computeHn(N)
    reply.send({ N, cardinality: ratios.length, ratios: ratios.map(({ a, b, value }) => ({ a, b, ratio: `${a}/${b}`, value })) })
  })

  app.get('/channels', {
    preHandler: requireScope('harmonic:compute'),
    schema: {
      tags: ['harmonic'],
      summary: 'Tabela de canais do HPM 1.0',
      querystring: { type: 'object', properties: { f0: { type: 'number', exclusiveMinimum: 0, default: HPM10_F0 } } },
    },
  }, async (req, reply) => {
    const { f0 = HPM10_F0 } = req.query as { f0?: number }
    reply.send({ f0, channels: channelTable(f0) })
  })

  app.post('/simulate', {
    preHandler: requireScope('harmonic:write'),
    schema: {
      tags: ['harmonic'],
      summary: 'Compõe os canais (HPM 1.0) ou razões a/b de H16 sobre f0 e registra a simulação',
    },
  }, async (req, reply) => {
    const parsed = SimulateBody.safeParse(req.body ?? {})
    if (!parsed.success) return badRequest(reply, 'Corpo inválido.', parsed.error.issues)
    const { f0, message } = parsed.data
    const harmonics = resolveHarmonics(parsed.data)
    if (typeof harmonics === 'string') return badRequest(reply, harmonics)

    const components = harmonics.map((h) => ({
      a: h.a, b: h.b, ratio: `${h.a}/${h.b}`,
      frequency_hz: frequencyOf(h.a, h.b, f0),
      amplitude: h.amplitude ?? 1.0, phase: h.phase ?? 0.0,
    }))

    await prisma.harmonicProtocolLog.create({
      data: {
        fundamentalFreq: f0,
        channels: JSON.stringify(components.map(({ a, b }) => ({ a, b }))),
        message: message ?? null,
      },
    })

    reply.send({ f0, components, timestamp: new Date().toISOString() })
  })

  app.post('/fft', {
    preHandler: requireScope('harmonic:compute'),
    schema: {
      tags: ['harmonic'],
      summary: 'Gera o sinal composto e decodifica os canais por FFT (porte de decode_fft)',
    },
  }, async (req, reply) => {
    const parsed = FftBody.safeParse(req.body ?? {})
    if (!parsed.success) return badRequest(reply, 'Corpo inválido.', parsed.error.issues)
    const { f0, sampleRate, duration, thresholdDb } = parsed.data
    const harmonics = resolveHarmonics(parsed.data)
    if (typeof harmonics === 'string') return badRequest(reply, harmonics)

    const n = Math.trunc(sampleRate * duration)
    const pot2 = n > 0 && (n & (n - 1)) === 0
    if (n < 16) return badRequest(reply, 'sampleRate × duration precisa gerar ao menos 16 amostras.')
    if (pot2 ? n > MAX_SAMPLES_POT2 : n > MAX_SAMPLES_DFT) {
      return badRequest(reply, `Amostras demais (${n}). Limite: ${MAX_SAMPLES_POT2} se potência de 2, ${MAX_SAMPLES_DFT} nos demais casos.`)
    }

    // Diferença deliberada em relação ao núcleo Python: componentes acima de Nyquist
    // seriam rebatidos (aliasing) e decodificados em frequências erradas; aqui são recusados.
    const nyquist = sampleRate / 2
    const acima = harmonics.filter((h) => frequencyOf(h.a, h.b, f0) >= nyquist)
    if (acima.length) {
      return badRequest(reply, `Componentes acima de Nyquist (${nyquist} Hz): ${acima.map((h) => `${h.a}/${h.b}`).join(', ')}. Aumente sampleRate.`)
    }

    const peaks = decodeFft(compositeSignal(f0, harmonics, duration, sampleRate), sampleRate, f0, thresholdDb)
    reply.send({
      f0, sampleRate, duration, samples: n, resolution_hz: sampleRate / n,
      transmitted: harmonics.map((h) => `${h.a}/${h.b}`),
      peaks,
      timestamp: new Date().toISOString(),
    })
  })
}
