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
export const ONS_BASE = 'https://ons-aws-prod-opendata.s3.sa-east-1.amazonaws.com/dataset/balanco_energia_subsistema_ho'
export const TIMEOUT_MS = 15_000
