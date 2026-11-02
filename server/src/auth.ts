import type { FastifyReply, FastifyRequest, preHandlerHookHandler } from 'fastify'
import { prisma } from './db'
import { hashKey, hashesMatch, parseKey, type Scope } from './keys'

export { SCOPES, generateKey, type Scope } from './keys'

// Chaves de API do Nautam. O banco guarda só o prefixo (para localizar a chave)
// e o SHA-256 da chave inteira. A chave em claro aparece uma única vez, na criação.

function extractKey(req: FastifyRequest): string | null {
  const header = req.headers['x-api-key']
  if (typeof header === 'string' && header.length > 0) return header.trim()
  const auth = req.headers.authorization
  if (typeof auth === 'string' && auth.startsWith('Bearer ')) return auth.slice(7).trim()
  return null
}

function deny(reply: FastifyReply, code: 401 | 403, message: string) {
  return reply.code(code).send({ error: code === 401 ? 'unauthorized' : 'forbidden', message })
}

// preHandler que exige uma chave válida, não revogada, não expirada e com o escopo pedido.
export function requireScope(scope: Scope): preHandlerHookHandler {
  return async function (req, reply) {
    const key = extractKey(req)
    if (!key) return deny(reply, 401, 'Chave de API ausente (cabeçalho x-api-key ou Authorization: Bearer).')
    const parsed = parseKey(key)
    if (!parsed) return deny(reply, 401, 'Chave de API inválida.')

    const record = await prisma.apiKey.findUnique({ where: { prefix: parsed.prefix } })
    if (!record || !hashesMatch(record.keyHash, hashKey(key))) {
      return deny(reply, 401, 'Chave de API inválida.')
    }
    if (record.revokedAt) return deny(reply, 401, 'Chave de API revogada.')
    if (record.expiresAt && record.expiresAt.getTime() <= Date.now()) {
      return deny(reply, 401, 'Chave de API expirada.')
    }
    if (!record.scopes.includes(scope)) {
      return deny(reply, 403, `Escopo necessário: ${scope}.`)
    }

    // Registro de uso sem bloquear a requisição; falha aqui não nega acesso.
    prisma.apiKey
      .update({ where: { id: record.id }, data: { lastUsedAt: new Date() } })
      .catch((err: unknown) => req.log.warn({ err }, 'falha ao registrar uso da chave'))
  }
}
