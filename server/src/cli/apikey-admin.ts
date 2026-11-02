// Núcleo da gestão de chaves, separado do CLI para poder ser testado.
//
// Regra de segurança: a chave em claro nunca vai para stdout em produção.
// Em produção, o CLI roda como tarefa avulsa do ECS e tudo o que ele imprime
// fica no CloudWatch Logs. Por isso a chave é entregue no Secrets Manager e o
// CLI imprime só a referência (ARN) do segredo.

import { generateKey, SCOPES, type Scope } from '../keys'

export type Entrega =
  | { tipo: 'secrets-manager'; nomeSegredo: string }
  | { tipo: 'stdout' } // só fora de produção (desenvolvimento local e CI)

export interface CriarOpcoes {
  name: string
  scopes: string[]
  expiresDays?: number
  entrega: Entrega
  producao: boolean
}

export interface Dependencias {
  apiKey: {
    create(args: { data: { name: string; prefix: string; keyHash: string; scopes: Scope[]; expiresAt: Date | null } }): Promise<{ id: string }>
    update(args: { where: { id: string }; data: { revokedAt: Date } }): Promise<unknown>
  }
  // Grava o valor num segredo novo e devolve o ARN.
  gravarSegredo(nome: string, valor: string, tags: Record<string, string>): Promise<string>
}

export interface Resultado {
  name: string
  prefix: string
  scopes: Scope[]
  expiresAt: Date | null
  secretArn?: string
  key?: string // presente só na entrega por stdout
}

// Nome de segredo aceito: /nautam/<ambiente>/apikeys/<nome>
const NOME_SEGREDO = /^\/nautam\/[a-z0-9-]+\/apikeys\/[A-Za-z0-9._-]{1,64}$/

export function validarOpcoes(o: CriarOpcoes): Scope[] {
  if (!o.name.trim()) throw new Error('--name é obrigatório')
  const scopes = o.scopes.map((s) => s.trim()).filter(Boolean)
  if (!scopes.length) throw new Error('--scopes é obrigatório')
  const invalid = scopes.filter((s) => !(SCOPES as readonly string[]).includes(s))
  if (invalid.length) throw new Error(`Escopos inválidos: ${invalid.join(', ')}. Válidos: ${SCOPES.join(', ')}`)
  if (o.expiresDays !== undefined && (!Number.isFinite(o.expiresDays) || o.expiresDays <= 0)) {
    throw new Error('--expires-days deve ser positivo')
  }
  if (o.entrega.tipo === 'stdout' && o.producao) {
    throw new Error('Em produção a chave não pode ir para stdout (acabaria no CloudWatch Logs). Use --secret-name.')
  }
  if (o.entrega.tipo === 'secrets-manager' && !NOME_SEGREDO.test(o.entrega.nomeSegredo)) {
    throw new Error('--secret-name deve seguir /nautam/<ambiente>/apikeys/<nome>')
  }
  return scopes as Scope[]
}

export async function criarChave(o: CriarOpcoes, deps: Dependencias): Promise<Resultado> {
  const scopes = validarOpcoes(o)
  const expiresAt = o.expiresDays ? new Date(Date.now() + o.expiresDays * 86_400_000) : null
  const { key, prefix, keyHash } = generateKey()
  const registro = await deps.apiKey.create({ data: { name: o.name, prefix, keyHash, scopes, expiresAt } })
  const base = { name: o.name, prefix, scopes, expiresAt }

  if (o.entrega.tipo === 'stdout') return { ...base, key }

  try {
    const secretArn = await deps.gravarSegredo(
      o.entrega.nomeSegredo,
      JSON.stringify({ key, prefix, name: o.name, scopes }),
      { projeto: 'nautam', recurso: 'apikey', prefixo: prefix },
    )
    return { ...base, secretArn }
  } catch (err) {
    // Sem segredo gravado, a chave seria irrecuperável: revoga para não deixar chave órfã ativa.
    await deps.apiKey.update({ where: { id: registro.id }, data: { revokedAt: new Date() } })
    throw new Error(`Falha ao gravar o segredo; chave ${prefix} revogada. Causa: ${err instanceof Error ? err.message : String(err)}`)
  }
}
