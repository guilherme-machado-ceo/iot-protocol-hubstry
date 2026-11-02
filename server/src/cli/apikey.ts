// Gestão de chaves de API do Nautam pela linha de comando.
//
//   node dist/cli/apikey.js create --name "parceiro-x" --scopes devices:read,devices:write [--expires-days 90]
//   node dist/cli/apikey.js list
//   node dist/cli/apikey.js revoke --prefix AbC12345
//
// Em produção, roda como tarefa avulsa do ECS com a mesma imagem da API,
// porque o banco é privado. A chave em claro só é exibida na criação.

import { prisma, disconnectPrisma } from '../db'
import { generateKey, SCOPES, type Scope } from '../keys'

function arg(name: string): string | undefined {
  const i = process.argv.indexOf(`--${name}`)
  return i >= 0 ? process.argv[i + 1] : undefined
}

async function create() {
  const name = arg('name')
  const scopesArg = arg('scopes')
  if (!name || !scopesArg) throw new Error('Uso: create --name <nome> --scopes <escopo,escopo> [--expires-days N]')
  const scopes = scopesArg.split(',').map((s) => s.trim()).filter(Boolean)
  const invalid = scopes.filter((s) => !(SCOPES as readonly string[]).includes(s))
  if (invalid.length) throw new Error(`Escopos inválidos: ${invalid.join(', ')}. Válidos: ${SCOPES.join(', ')}`)
  const days = arg('expires-days')
  const expiresAt = days ? new Date(Date.now() + Number(days) * 86_400_000) : null
  if (days && (!Number.isFinite(Number(days)) || Number(days) <= 0)) throw new Error('--expires-days deve ser positivo')

  const { key, prefix, keyHash } = generateKey()
  await prisma.apiKey.create({ data: { name, prefix, keyHash, scopes: scopes as Scope[], expiresAt } })
  console.log(JSON.stringify({ name, prefix, scopes, expiresAt, key }, null, 2))
  console.error('Guarde a chave agora: ela não será exibida de novo.')
}

async function list() {
  const keys = await prisma.apiKey.findMany({ orderBy: { createdAt: 'desc' } })
  for (const k of keys) {
    console.log(
      [k.prefix, k.name, k.scopes.join(','), k.revokedAt ? 'revogada' : 'ativa',
        k.expiresAt?.toISOString() ?? 'sem-expiração', k.lastUsedAt?.toISOString() ?? 'nunca-usada'].join(' | '),
    )
  }
}

async function revoke() {
  const prefix = arg('prefix')
  if (!prefix) throw new Error('Uso: revoke --prefix <prefixo>')
  const r = await prisma.apiKey.updateMany({ where: { prefix, revokedAt: null }, data: { revokedAt: new Date() } })
  console.log(r.count === 1 ? `Chave ${prefix} revogada.` : `Nenhuma chave ativa com prefixo ${prefix}.`)
  if (r.count !== 1) process.exitCode = 1
}

async function main() {
  const cmd = process.argv[2]
  if (cmd === 'create') await create()
  else if (cmd === 'list') await list()
  else if (cmd === 'revoke') await revoke()
  else throw new Error('Comandos: create | list | revoke')
}

main()
  .catch((err) => {
    console.error(err instanceof Error ? err.message : err)
    process.exitCode = 1
  })
  .finally(() => disconnectPrisma())
