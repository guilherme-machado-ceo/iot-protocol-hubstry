// Contrato comum das fontes do Nautam Live.
export interface Observacao {
  provider: 'openaq' | 'ons'
  stationRef: string
  sensorRef: string   // identificador estável da série
  parameter: string
  value: number
  unit: string
  observedAt: Date    // UTC
  locality: string | null
  licenseName: string
  licenseUrl: string
  attribution: string
  sourceUrl: string
}

export interface ResultadoFonte {
  fonte: string
  observacoes: Observacao[]
  rejeitadas: { ref: string; motivo: string }[]
}

export type Fetch = typeof fetch
