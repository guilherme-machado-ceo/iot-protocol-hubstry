import { createHash, randomBytes, timingSafeEqual } from 'node:crypto'

// Funções puras das chaves de API (sem banco), testáveis isoladamente.
// Formato: nk_<prefixo de 8 caracteres>_<segredo de 43 caracteres>

export const SCOPES = ['devices:read', 'devices:write', 'harmonic:write', 'harmonic:compute'] as const
export type Scope = (typeof SCOPES)[number]

const KEY_PATTERN = /^nk_([A-Za-z0-9]{8})_([A-Za-z0-9_-]{43})$/

function base62(len: number): string {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  const bytes = randomBytes(len * 2)
  let out = ''
  for (let i = 0; i < bytes.length && out.length < len; i++) {
    // rejeição para evitar viés de módulo
    if (bytes[i] < 248) out += alphabet[bytes[i] % 62]
  }
  return out.length === len ? out : base62(len)
}

export function hashKey(key: string): string {
  return createHash('sha256').update(key, 'utf8').digest('hex')
}

export function generateKey(): { key: string; prefix: string; keyHash: string } {
  const prefix = base62(8)
  const secret = randomBytes(32).toString('base64url') // 43 caracteres
  const key = `nk_${prefix}_${secret}`
  return { key, prefix, keyHash: hashKey(key) }
}

export function parseKey(key: string): { prefix: string } | null {
  const m = KEY_PATTERN.exec(key)
  return m ? { prefix: m[1] } : null
}

export function hashesMatch(a: string, b: string): boolean {
  const ba = Buffer.from(a, 'hex')
  const bb = Buffer.from(b, 'hex')
  return ba.length === bb.length && timingSafeEqual(ba, bb)
}

