import { describe, expect, it } from 'vitest'
import { generateKey, hashKey, hashesMatch, parseKey } from '../../src/keys'

describe('chaves de API', () => {
  it('gera chave no formato nk_<8>_<43> com hash SHA-256', () => {
    const { key, prefix, keyHash } = generateKey()
    expect(key).toMatch(/^nk_[A-Za-z0-9]{8}_[A-Za-z0-9_-]{43}$/)
    expect(parseKey(key)?.prefix).toBe(prefix)
    expect(keyHash).toMatch(/^[0-9a-f]{64}$/)
    expect(hashKey(key)).toBe(keyHash)
  })

  it('não repete chaves nem prefixos em 1.000 gerações', () => {
    const keys = new Set<string>()
    const prefixes = new Set<string>()
    for (let i = 0; i < 1000; i++) {
      const g = generateKey()
      keys.add(g.key)
      prefixes.add(g.prefix)
    }
    expect(keys.size).toBe(1000)
    expect(prefixes.size).toBe(1000)
  })

  it('rejeita formatos inválidos', () => {
    for (const bad of ['', 'nk_', 'nk_short_x', 'xx_AAAAAAAA_' + 'a'.repeat(43), 'nk_AAAAAAAA_' + 'a'.repeat(42)]) {
      expect(parseKey(bad)).toBeNull()
    }
  })

  it('compara hashes em tempo constante e detecta divergência', () => {
    const a = generateKey().keyHash
    const b = generateKey().keyHash
    expect(hashesMatch(a, a)).toBe(true)
    expect(hashesMatch(a, b)).toBe(false)
    expect(hashesMatch(a, a.slice(0, 10))).toBe(false)
  })
})
