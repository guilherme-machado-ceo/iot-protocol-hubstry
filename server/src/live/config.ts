// Séries do Nautam Live. Escolhidas pela qualificação de 03/11/2026
// (deploy/live/qualificar-openaq.sh US): monitores oficiais AirNow, fixos,
// ativos e com licença de domínio público. No Brasil, 0 de 113 estações da
// OpenAQ eram elegíveis; o Brasil entra pelo ONS (energia).
export const SERIES_OPENAQ: { location: number; parameter: string }[] = [
  { location: 162, parameter: 'pm25' },
  { location: 162, parameter: 'o3' },
  { location: 212, parameter: 'pm10' },
  { location: 212, parameter: 'no2' },
  { location: 213, parameter: 'pm25' },
  { location: 215, parameter: 'o3' },
  { location: 216, parameter: 'no2' },
  { location: 217, parameter: 'pm25' },
]

// Balanço de energia horário do ONS, sistema nacional (SIN). Licença CC BY 4.0.
export const SERIES_ONS: { subsistema: string; coluna: string; parameter: string }[] = [
  { subsistema: 'SIN', coluna: 'val_carga', parameter: 'carga' },
  { subsistema: 'SIN', coluna: 'val_gerhidraulica', parameter: 'geracao_hidraulica' },
  { subsistema: 'SIN', coluna: 'val_gereolica', parameter: 'geracao_eolica' },
  { subsistema: 'SIN', coluna: 'val_gersolar', parameter: 'geracao_solar' },
]

export const OPENAQ_BASE = 'https://api.openaq.org/v3'
export const ONS_BUCKET = 'ons-aws-prod-opendata'
export const ONS_PREFIXO = 'dataset/balanco_energia_subsistema_ho'
// Endpoint global; se o S3 responder 301, o adaptador usa a região indicada.
export const ONS_BASE = `https://${ONS_BUCKET}.s3.amazonaws.com/${ONS_PREFIXO}`
export const TIMEOUT_MS = 15_000

// Idade máxima de uma leitura para entrar no quadro e no painel (horas).
// Ar: valores horários; 48 h toleram atrasos da agência. Energia: o ONS publica
// com 1 a 2 dias de defasagem; 72 h toleram fins de semana.
export const IDADE_MAXIMA_H: Record<'openaq' | 'ons', number> = { openaq: 48, ons: 72 }
export function idadeHoras(observedAt: Date, agora: Date): number {
  return (agora.getTime() - observedAt.getTime()) / 3_600_000
}
