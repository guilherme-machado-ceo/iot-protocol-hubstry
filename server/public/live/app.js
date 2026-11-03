// Painel do Nautam Live. Sem dependências; servido como arquivo separado por causa da CSP.
'use strict'

const NOMES = {
  pm25: 'PM2,5 (partículas finas)',
  pm10: 'PM10 (partículas inaláveis)',
  o3: 'O3 (ozônio)',
  no2: 'NO2 (dióxido de nitrogênio)',
  carga: 'Carga do SIN',
  geracao_hidraulica: 'Geração hidráulica',
  geracao_eolica: 'Geração eólica',
  geracao_solar: 'Geração solar',
}
const ESTADOS = { normal: 'ao vivo', desatualizado: 'desatualizado', falha: 'última execução falhou', sem_dados: 'sem dados', carregando: 'carregando…' }

const estado = { janela: '24h', serie: null, dados: null }
const $ = (s) => document.querySelector(s)

function el(tag, attrs, ...filhos) {
  const e = document.createElement(tag)
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null) continue
    if (k === 'class') e.className = v
    else e.setAttribute(k, v)
  }
  for (const f of filhos) if (f != null) e.append(f instanceof Node ? f : String(f))
  return e
}

function num(v, casas) {
  if (v == null || !Number.isFinite(v)) return '—'
  return v.toLocaleString('pt-BR', { minimumFractionDigits: casas, maximumFractionDigits: casas })
}
function casasPara(unidade) { return unidade === 'ppm' ? 3 : unidade === 'MWmed' ? 0 : 1 }
function pct(v) { return v == null ? '—' : `${num(v * 100, v === 1 ? 0 : 1)}%` }
function utc(iso) { return iso ? new Date(iso).toISOString().slice(0, 16).replace('T', ' ') : '—' }
function nomeSerie(chave, leitura) {
  const [prov, est, par] = chave.split(':')
  const base = NOMES[par] || par
  if (prov === 'ons') return { nome: base, meta: 'ONS · Brasil' }
  return { nome: base, meta: `${leitura && leitura.locality ? leitura.locality : 'estação ' + est} · EUA` }
}

function indicador(rotulo, valor, sub, classe) {
  return el('div', { class: 'indicador' }, el('div', { class: 'rotulo' }, rotulo), el('div', { class: `valor ${classe || ''}` }, valor), sub ? el('div', { class: 'sub' }, sub) : null)
}

function renderEstado(d) {
  const e = $('#estado')
  e.dataset.estado = d.estado
  e.textContent = ESTADOS[d.estado] || d.estado
  if (d.ultimaExecucaoOk) e.title = `Última execução bem-sucedida: ${utc(d.ultimaExecucaoOk.concluidaEm)} UTC`
  $('#declaracao').textContent = d.declaracao
  $('#gerado-em').textContent = `Resumo gerado em ${utc(d.geradoEm)} UTC. Atualiza a cada minuto.`
}

function renderIndicadores(d) {
  const box = $('#indicadores')
  box.replaceChildren()
  const p = d.protocolo
  if (!p) { box.append(indicador('Protocolo', 'sem execução', null)); return }
  const ex = p.metricas.execucao
  const q = p.metricas.quadro
  const menor = p.metricas.varredura.menorSnrTestadaDb
  box.append(
    indicador('Canais recuperados (recall)', pct(ex.recall), `${ex.tp} de ${ex.tp + ex.fn} leituras`, ex.recall >= 0.95 ? 'ok' : 'ruim'),
    indicador('Precisão', pct(ex.precisao), `${ex.fp} falsos positivos`, ex.precisao >= 0.99 ? 'ok' : 'ruim'),
    indicador('Erro médio de amplitude', num(ex.maeAmplitude, 4), 'escala 0,1 a 1,0'),
    indicador('SNR medida', `${num(p.snrMedidoDb, 1)} dB`, `solicitada ${num(p.snrSolicitadoDb, 0)} dB`),
    indicador('Menor SNR aprovada', menor.receptorHpm == null ? 'nenhuma' : `${menor.receptorHpm} dB`, `cego: ${menor.decodificadorCego == null ? 'nenhuma' : menor.decodificadorCego + ' dB'}`),
    indicador('Leituras por quadro', String(q.valoresPorQuadro), `${num(q.valoresPorSegundoSimulado, 0)} valores/s simulados`),
  )
  const cego = p.canais.decodificadorCego
  $('#nota-execucao').textContent = `Execução de ${utc(p.slotUtc)} UTC, semente ${p.semente}. Na mesma execução, o decodificador cego encontrou ${cego.picosTotais} picos, dos quais ${cego.falsos} falsos.`
}

function renderLeituras(d) {
  const tb = $('#leituras tbody')
  tb.replaceChildren()
  const rx = new Map(((d.protocolo && d.protocolo.canais.receptorHpm) || []).map((r) => [r.chave, r]))
  for (const l of d.leituras) {
    const r = rx.get(l.chave)
    const { nome, meta } = nomeSerie(l.chave, l)
    const casas = casasPara(l.unit)
    const tr = el('tr', { 'data-chave': l.chave, 'aria-selected': String(l.chave === estado.serie), tabindex: '0' },
      el('td', null, el('div', { class: 'serie-nome' }, nome), el('div', { class: 'serie-meta' }, meta)),
      el('td', null, r ? el('span', { class: 'canal' }, `${r.canal} · ${r.razao}`) : '—'),
      el('td', { class: 'num' }, `${num(l.value, casas)} ${l.unit}`),
      el('td', { class: 'num' }, r && r.valorRecuperado != null ? `${num(r.valorRecuperado, casas)} ${l.unit}` : '—'),
      el('td', null, utc(l.observedAt)),
      el('td', { class: 'fonte' }, el('a', { href: l.sourceUrl, rel: 'noopener' }, l.attribution), el('br'), el('a', { href: l.licenseUrl, rel: 'noopener' }, l.licenseName), el('br'), l.natureza),
    )
    const escolher = () => { estado.serie = l.chave; $('#sel-serie').value = l.chave; marcarLinha(); carregarSerie() }
    tr.addEventListener('click', (ev) => { if (ev.target.tagName !== 'A') escolher() })
    tr.addEventListener('keydown', (ev) => { if (ev.key === 'Enter') escolher() })
    tb.append(tr)
  }
}

function marcarLinha() {
  for (const tr of document.querySelectorAll('#leituras tbody tr')) tr.setAttribute('aria-selected', String(tr.dataset.chave === estado.serie))
}

function renderVarredura(d) {
  const tb = $('#varredura tbody')
  tb.replaceChildren()
  if (!d.protocolo) return
  const v = d.protocolo.metricas.varredura
  for (const l of v.linhas) {
    const ok = (l.receptorHpm.recall ?? 0) >= 0.95 && (l.receptorHpm.precisao ?? 0) >= 0.99
    tb.append(el('tr', null,
      el('td', { class: 'num' }, String(l.snrDb)),
      el('td', { class: `num ${ok ? 'ok' : 'ruim'}` }, pct(l.receptorHpm.recall)),
      el('td', { class: `num ${ok ? 'ok' : 'ruim'}` }, pct(l.receptorHpm.precisao)),
      el('td', { class: 'num' }, num(l.decodificadorCego.falsosPorQuadro, 1)),
    ))
  }
  const viz = d.protocolo.metricas.vizinhos || []
  $('#nota-varredura').textContent = viz.length
    ? `Canais mais próximos: ${viz.map((p) => `${p.par} (${num(p.separacaoBins, 1)} bins, recall ${pct(p.recall)})`).join('; ')}. Um bin equivale a 64 Hz.`
    : ''
}

function renderMqtt(d) {
  const box = $('#mqtt')
  box.replaceChildren()
  const m = d.protocolo && d.protocolo.mqtt
  if (!m) return
  box.append(
    indicador('Conteúdo (JSON)', `${m.payloadBytes} B`, 'mesmas leituras do quadro'),
    indicador('PUBLISH QoS 0', `${m.publishQos0Bytes} B`, `${m.overheadQos0Bytes} B de cabeçalho`),
    indicador('PUBLISH + PUBACK QoS 1', `${m.trocaQos1Bytes} B`, `${m.overheadQos1Bytes} B de cabeçalho`),
    indicador('Quadro Nautam (float64)', `${m.vetorAmostrasFloat64Bytes} B`, '2.048 amostras, sem compressão'),
  )
  box.append(el('p', { class: 'nota', style: 'grid-column: 1 / -1; background: var(--painel); margin: 0; padding: 12px 16px; max-width: none' }, `Fora da conta: ${m.exclui}.`))
}

function renderSeletor(d) {
  const sel = $('#sel-serie')
  if (sel.options.length) return
  const porChave = new Map(d.leituras.map((l) => [l.chave, l]))
  for (const chave of d.series) {
    const { nome, meta } = nomeSerie(chave, porChave.get(chave))
    sel.append(el('option', { value: chave }, `${nome} · ${meta}`))
  }
  estado.serie = estado.serie || d.series[d.series.length - 4] || d.series[0]
  sel.value = estado.serie
  sel.addEventListener('change', () => { estado.serie = sel.value; marcarLinha(); carregarSerie() })
}

const SVG = 'http://www.w3.org/2000/svg'
function svg(tag, attrs) {
  const e = document.createElementNS(SVG, tag)
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v)
  return e
}

function renderGrafico(pontos, unidade) {
  const box = $('#grafico')
  box.replaceChildren()
  const leg = $('#legenda-grafico')
  if (!pontos.length) { box.append(el('p', { class: 'nota' }, 'Sem leituras nesta janela.')); leg.textContent = ''; return }
  const W = 1000, H = 240, m = { e: 64, d: 12, t: 12, b: 28 }
  const xs = pontos.map((p) => new Date(p.t).getTime())
  const ys = pontos.map((p) => p.v)
  const x0 = Math.min(...xs), x1 = Math.max(...xs)
  let y0 = Math.min(...ys), y1 = Math.max(...ys)
  if (y0 === y1) { y0 -= 1; y1 += 1 }
  const pad = (y1 - y0) * 0.08; y0 -= pad; y1 += pad
  const X = (t) => m.e + (x1 === x0 ? 0.5 : (t - x0) / (x1 - x0)) * (W - m.e - m.d)
  const Y = (v) => m.t + (1 - (v - y0) / (y1 - y0)) * (H - m.t - m.b)
  const s = svg('svg', { viewBox: `0 0 ${W} ${H}`, preserveAspectRatio: 'none', role: 'img', 'aria-label': `Série histórica em ${unidade}` })
  const casas = casasPara(unidade)
  for (let i = 0; i <= 3; i++) {
    const v = y0 + ((y1 - y0) * i) / 3
    s.append(svg('line', { x1: m.e, x2: W - m.d, y1: Y(v), y2: Y(v), stroke: '#2a2b1c', 'stroke-width': 1 }))
    const t = svg('text', { x: m.e - 8, y: Y(v) + 4, 'text-anchor': 'end', fill: '#b9b9ad', 'font-size': 12, 'font-family': 'ui-monospace, monospace' })
    t.textContent = num(v, casas); s.append(t)
  }
  for (const [t, ancora] of [[x0, 'start'], [x1, 'end']]) {
    const tx = svg('text', { x: X(t), y: H - 6, 'text-anchor': ancora, fill: '#b9b9ad', 'font-size': 12, 'font-family': 'ui-monospace, monospace' })
    tx.textContent = utc(new Date(t).toISOString()); s.append(tx)
  }
  const d = pontos.map((p, i) => `${i ? 'L' : 'M'}${X(xs[i]).toFixed(1)},${Y(p.v).toFixed(1)}`).join('')
  s.append(svg('path', { d, fill: 'none', stroke: '#00ffff', 'stroke-width': 2, 'vector-effect': 'non-scaling-stroke', 'stroke-linejoin': 'round' }))
  const u = pontos.length - 1
  s.append(svg('circle', { cx: X(xs[u]), cy: Y(ys[u]), r: 4, fill: '#ff6605' }))
  box.append(s)
  leg.textContent = `${pontos.length} pontos em ${unidade}, horário UTC. ${estado.janela === '24h' ? 'Leituras individuais.' : 'Médias horárias.'} Último valor: ${num(ys[u], casas)} ${unidade}.`
}

async function carregarSerie() {
  if (!estado.serie) return
  try {
    const r = await fetch(`/api/live/public?window=${estado.janela}&series=${encodeURIComponent(estado.serie)}`)
    const d = await r.json()
    const l = d.leituras.find((x) => x.chave === estado.serie)
    renderGrafico(d.pontos || [], l ? l.unit : '')
  } catch {
    $('#grafico').replaceChildren(el('p', { class: 'nota' }, 'Não foi possível carregar o histórico.'))
  }
}

async function carregar() {
  try {
    const r = await fetch('/api/live/public')
    if (!r.ok) throw new Error(String(r.status))
    const d = await r.json()
    estado.dados = d
    renderEstado(d); renderIndicadores(d); renderLeituras(d); renderVarredura(d); renderMqtt(d); renderSeletor(d)
  } catch {
    const e = $('#estado'); e.dataset.estado = 'falha'; e.textContent = 'API indisponível'
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  for (const b of document.querySelectorAll('.janelas button')) {
    b.addEventListener('click', () => {
      estado.janela = b.dataset.janela
      for (const o of document.querySelectorAll('.janelas button')) o.setAttribute('aria-pressed', String(o === b))
      carregarSerie()
    })
  }
  await carregar()
  carregarSerie()
  setInterval(carregar, 60_000)
})
