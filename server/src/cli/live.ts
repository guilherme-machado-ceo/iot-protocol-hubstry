// Nautam Live — job de ingestão (E1).
//   node dist/cli/live.js run [--slot 2026-11-03T12:05:00Z]
// Em produção roda como tarefa ECS agendada; OPENAQ_API_KEY vem do Secrets Manager.
// Imprime um resumo JSON sem segredos e sai com código 1 se o slot falhar.
import { prisma, disconnectPrisma } from '../db'
import { executar } from '../live/ingestao'

function arg(n: string): string | undefined {
  const i = process.argv.indexOf(`--${n}`)
  return i >= 0 ? process.argv[i + 1] : undefined
}

async function main() {
  if (process.argv[2] !== 'run') throw new Error('Uso: live run [--slot ISO]')
  const s = arg('slot')
  const slot = s ? new Date(s) : undefined
  if (slot && Number.isNaN(slot.getTime())) throw new Error('--slot inválido')
  const r = await executar(prisma, { slot, chaveOpenAQ: process.env.OPENAQ_API_KEY?.trim() || undefined })
  console.log(JSON.stringify(r))
  if (r.status === 'failed') process.exitCode = 1
}

main()
  .catch((err) => { console.error(err instanceof Error ? err.message : err); process.exitCode = 1 })
  .finally(() => disconnectPrisma())
