// Job de ingestão do Nautam Live (E1). Uma execução por intervalo de 5 min:
// reivindica o slot (único no banco), coleta as fontes, grava só leituras novas
// e registra o resultado. Execuções concorrentes no mesmo slot não duplicam.
import { coletarOpenAQ } from './openaq'
import { coletarONS } from './ons'
import type { Fetch, Observacao, ResultadoFonte } from './tipos'

export const MINUTOS_SLOT = 5

export function slotDe(d: Date): Date {
  const ms = MINUTOS_SLOT * 60_000
  return new Date(Math.floor(d.getTime() / ms) * ms)
}

export interface BancoLive {
  liveRun: {
    create(a: { data: { slotUtc: Date; status: string; sources: string[] } }): Promise<{ id: number }>
    update(a: { where: { id: number }; data: Record<string, unknown> }): Promise<unknown>
  }
  liveObservation: {
    createMany(a: { data: (Observacao & { firstRunId: number })[]; skipDuplicates: boolean }): Promise<{ count: number }>
  }
}

export interface Resumo {
  slot: string
  status: 'succeeded' | 'no_new_data' | 'failed' | 'slot_ocupado'
  runId?: number
  coletadas: number
  novas: number
  rejeitadas: { ref: string; motivo: string }[]
}

function slotOcupado(err: unknown): boolean {
  return typeof err === 'object' && err !== null && (err as { code?: string }).code === 'P2002'
}

export async function executar(
  db: BancoLive,
  opts: { agora?: Date; slot?: Date; chaveOpenAQ?: string; f?: Fetch } = {},
): Promise<Resumo> {
  const slot = opts.slot ?? slotDe(opts.agora ?? new Date())
  const base = { slot: slot.toISOString(), coletadas: 0, novas: 0, rejeitadas: [] as Resumo['rejeitadas'] }

  let runId: number
  try {
    runId = (await db.liveRun.create({ data: { slotUtc: slot, status: 'running', sources: ['openaq', 'ons'] } })).id
  } catch (err) {
    if (slotOcupado(err)) return { ...base, status: 'slot_ocupado' }
    throw err
  }

  try {
    const f = opts.f ?? fetch
    const resultados: ResultadoFonte[] = []
    if (opts.chaveOpenAQ) resultados.push(await coletarOpenAQ(opts.chaveOpenAQ, f))
    else resultados.push({ fonte: 'openaq', observacoes: [], rejeitadas: [{ ref: 'openaq', motivo: 'OPENAQ_API_KEY ausente' }] })
    resultados.push(await coletarONS(f, opts.agora ?? new Date()))

    const obs = resultados.flatMap((r) => r.observacoes)
    const rejeitadas = resultados.flatMap((r) => r.rejeitadas)
    const { count } = obs.length
      ? await db.liveObservation.createMany({ data: obs.map((o) => ({ ...o, firstRunId: runId })), skipDuplicates: true })
      : { count: 0 }
    const status = obs.length === 0 ? 'failed' : count === 0 ? 'no_new_data' : 'succeeded'
    const maisRecente = obs.reduce<Date | null>((m, o) => (!m || o.observedAt > m ? o.observedAt : m), null)

    await db.liveRun.update({
      where: { id: runId },
      data: {
        status, newObservations: count, sourceObservedAt: maisRecente, completedAt: new Date(),
        errorCode: obs.length === 0 ? 'sem_dados' : null,
        errorDetail: rejeitadas.length ? JSON.stringify(rejeitadas).slice(0, 2000) : null,
      },
    })
    return { ...base, status, runId, coletadas: obs.length, novas: count, rejeitadas }
  } catch (err) {
    await db.liveRun.update({
      where: { id: runId },
      data: { status: 'failed', completedAt: new Date(), errorCode: 'excecao', errorDetail: String(err).slice(0, 2000) },
    })
    throw err
  }
}
