// Gestão de chaves de API do Nautam pela linha de comando.
//
// Produção (tarefa avulsa do ECS; a chave vai para o Secrets Manager e só o ARN é impresso):
//   node dist/cli/apikey.js create --name parceiro-x --scopes devices:read,devices:write \
//     --secret-name /nautam/production/apikeys/parceiro-x [--expires-days 90]
//
// Desenvolvimento local e CI (só com NODE_ENV=test ou development; qualquer outro valor, ou ausente, recusa):
//   NODE_ENV=development node dist/cli/apikey.js create --name dev --scopes devices:read --stdout
//
//   node dist/cli/apikey.js list
//   node dist/cli/apikey.js revoke --prefix AbC12345
//
// Para ler a chave entregue em produção, quem tem acesso ao segredo roda:
//   aws secretsmanager get-secret-value --secret-id <ARN> --query SecretString --output text

import { prisma, disconnectPrisma } from '../db'
import { criarChave, type Entrega } from './apikey-admin'

function arg(name: string): string | undefined {
  const i = process.argv.indexOf(`--${name}`)
  return i >= 0 ? process.argv[i + 1] : undefined
}

async function gravarSegredo(nome: string, valor: string, tags: Record<string, string>): Promise<string> {
  const { SecretsManagerClient, CreateSecretCommand } = await import('@aws-sdk/client-secrets-manager')
  const client = new SecretsManagerClient({})
  const r = await client.send(new CreateSecretCommand({
    Name: nome,
    SecretString: valor,
    Description: 'Chave de API do Nautam (gerada pelo CLI apikey)',
    Tags: Object.entries(tags).map(([Key, Value]) => ({ Key, Value })),
  }))
  if (!r.ARN) throw new Error('Secrets Manager não devolveu o ARN')
  return r.ARN
}

async function create() {
  const secretName = arg('secret-name')
  const stdout = process.argv.includes('--stdout')
  if (Boolean(secretName) === stdout) throw new Error('Informe exatamente um destino: --secret-name <nome> ou --stdout')
  const entrega: Entrega = secretName ? { tipo: 'secrets-manager', nomeSegredo: secretName } : { tipo: 'stdout' }
  const days = arg('expires-days')

  const r = await criarChave({
    name: arg('name') ?? '',
    scopes: (arg('scopes') ?? '').split(','),
    expiresDays: days === undefined ? undefined : Number(days),
    entrega,
    ambiente: process.env.NODE_ENV,
  }, { apiKey: prisma.apiKey, gravarSegredo })

  console.log(JSON.stringify(r, null, 2))
  if (r.key) console.error('Guarde a chave agora: ela não será exibida de novo.')
  else console.error(`Chave entregue no segredo ${r.secretArn}. Nada sensível foi impresso.`)
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
