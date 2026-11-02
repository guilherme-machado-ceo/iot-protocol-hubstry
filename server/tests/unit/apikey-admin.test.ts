import { describe, expect, it, vi } from 'vitest'
import { criarChave, type CriarOpcoes, type Dependencias } from '../../src/cli/apikey-admin'
import { hashKey } from '../../src/keys'

function deps(falhaSegredo = false) {
  const criadas: { prefix: string; keyHash: string }[] = []
  const revogadas: number[] = []
  const segredos: { nome: string; valor: string }[] = []
  const d: Dependencias = {
    apiKey: {
      create: vi.fn(async ({ data }) => { criadas.push(data); return { id: criadas.length } }),
      update: vi.fn(async ({ where }) => { revogadas.push(where.id); return {} }),
    },
    gravarSegredo: vi.fn(async (nome: string, valor: string) => {
      if (falhaSegredo) throw new Error('AccessDenied')
      segredos.push({ nome, valor })
      return `arn:aws:secretsmanager:sa-east-1:000000000000:secret:${nome}-AbCdEf`
    }),
  }
  return { d, criadas, revogadas, segredos }
}

const base: Omit<CriarOpcoes, 'entrega' | 'producao'> = { name: 'parceiro-x', scopes: ['harmonic:write'] }
const SM = { tipo: 'secrets-manager' as const, nomeSegredo: '/nautam/production/apikeys/parceiro-x' }

describe('entrega segura da chave (auditoria da Luna)', () => {
  it('em produção, recusa stdout antes de criar qualquer chave', async () => {
    const { d, criadas } = deps()
    await expect(criarChave({ ...base, entrega: { tipo: 'stdout' }, producao: true }, d)).rejects.toThrow(/CloudWatch/)
    expect(criadas).toHaveLength(0)
  })

  it('com Secrets Manager, o resultado impresso não contém a chave', async () => {
    const { d, criadas, segredos } = deps()
    const r = await criarChave({ ...base, entrega: SM, producao: true }, d)
    expect(r.key).toBeUndefined()
    expect(r.secretArn).toMatch(/^arn:aws:secretsmanager:/)
    // O segredo guarda a chave, e ela confere com o hash gravado no banco.
    const { key } = JSON.parse(segredos[0].valor)
    expect(hashKey(key)).toBe(criadas[0].keyHash)
    expect(JSON.stringify(r)).not.toContain(key)
  })

  it('se gravar o segredo falhar, a chave é revogada (não fica chave órfã ativa)', async () => {
    const { d, criadas, revogadas } = deps(true)
    await expect(criarChave({ ...base, entrega: SM, producao: true }, d)).rejects.toThrow(/revogada/)
    expect(revogadas).toEqual([1])
  })

  it('nome de segredo fora da convenção é recusado', async () => {
    const { d, criadas } = deps()
    await expect(criarChave({ ...base, entrega: { tipo: 'secrets-manager', nomeSegredo: 'qualquer' }, producao: true }, d)).rejects.toThrow(/apikeys/)
    expect(criadas).toHaveLength(0)
  })

  it('fora de produção, stdout entrega a chave (desenvolvimento e CI)', async () => {
    const { d, criadas } = deps()
    const r = await criarChave({ ...base, entrega: { tipo: 'stdout' }, producao: false }, d)
    expect(hashKey(r.key!)).toBe(criadas[0].keyHash)
  })

  it('escopo inválido e validade não positiva são recusados', async () => {
    const { d } = deps()
    await expect(criarChave({ ...base, scopes: ['admin'], entrega: SM, producao: true }, d)).rejects.toThrow(/inválidos/)
    await expect(criarChave({ ...base, expiresDays: 0, entrega: SM, producao: true }, d)).rejects.toThrow(/positivo/)
  })
})
