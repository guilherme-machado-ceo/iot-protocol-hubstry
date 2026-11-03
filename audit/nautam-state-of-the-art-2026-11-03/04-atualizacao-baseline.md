# Atualização de baseline da auditoria do Nautam

**Data da atualização:** 03/11/2026
**Baseline histórico preservado:** [`main@71fb8ea03241f48d1a63e3cc356ae07c8e094948`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/tree/71fb8ea03241f48d1a63e3cc356ae07c8e094948)
**Novo baseline incorporado:** [`main@7ec77b6d839588e49d87906f1d6d931ed419376a`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/tree/7ec77b6d839588e49d87906f1d6d931ed419376a)
**Alteração pendente:** [Pull Request (PR, solicitação de incorporação) #56](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/pull/56), `fix/zod-4@4104f656eb2208da4def781448b3672b75857b7a`.

**Convenções terminológicas:** Application Programming Interface (API, interface de programação de aplicações); Amazon Web Services (AWS, serviços web da Amazon); Continuous Integration (CI, integração contínua); Operador Nacional do Sistema Elétrico (ONS).

## 1. Finalidade e relação com os relatórios anteriores

Os documentos `00` a `03` permanecem inalterados como registro da auditoria executada sobre `main@71fb8ea`. Este adendo registra as mudanças incorporadas depois desse corte, corrige o diagnóstico dos workflows e reorganiza as prioridades. Ele não substitui a derivação matemática, a análise de estado da arte nem a matriz original.

A revisão independente relatada pela Luna corroborou três resultados por cálculo e inspeção separados:

- a definição quadrada do conjunto H16 enumera 159 razões, enquanto `cardinality_hn()` devolve 80;
- cinco canais da tabela HPM 1.0, nome adotado pelo projeto para a tabela fixa de 12 canais, não são coerentes na janela atual de 2.048 amostras;
- a correlação cruzada máxima calculada é aproximadamente `0,0065` nessa janela e cai para erro numérico numa janela coerente de 480 amostras;
- Zod 3.25.76 está abrangido pelo aviso HIGH de consumo de memória [GHSA-mrhx-c7xc-m3w5](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5).

Essas confirmações reforçam, mas não substituem, as evidências primárias citadas nos relatórios: código, testes, logs e cálculos reproduzíveis.

## 2. Novo baseline e mudanças posteriores

### 2.1 PR #54 — rótulos e separação das métricas

O [PR #54](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/pull/54) foi incorporado pelo commit [`ffb5af85c50d2435f89afa5d7aea11a0fd336d29`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/commit/ffb5af85c50d2435f89afa5d7aea11a0fd336d29). Ele alterou apenas:

- `server/public/live/app.css`;
- `server/public/live/app.js`;
- `server/public/live/index.html`.

O painel passou a separar:

1. cobertura de séries no quadro;
2. detecção de canais, com recall e precisão;
3. fidelidade dos valores;
4. canal simulado e relação sinal-ruído;
5. tamanho estimado da mensagem Message Queuing Telemetry Transport (MQTT, transporte de telemetria por fila de mensagens).

Também passou a explicar que a varredura usa quadros sintéticos de referência e que a comparação MQTT não mede energia ou eficiência de comunicação. A fórmula de fidelidade introduzida no navegador,

```text
|amplitudeRecebida − amplitudeEnviada| / 0,9 ≤ 0,02
```

é coerente com ±2% da faixa declarada para canais detectados. Ela mede a amplitude efetivamente transmitida depois de eventual saturação e não inclui canais perdidos no denominador. O PR melhora a comunicação, mas não altera o receptor, o pipeline de dados nem os limites científicos.

### 2.2 PR #55 — contexto de cadência e escopo da fidelidade

O [PR #55](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/pull/55) foi incorporado pelo novo baseline [`7ec77b6d839588e49d87906f1d6d931ed419376a`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/commit/7ec77b6d839588e49d87906f1d6d931ed419376a). Ele esclareceu que:

- o Nautam Live consulta fontes a cada cinco minutos, mas cada fonte possui cadência própria e nem toda consulta obtém uma nova medição;
- a métrica de ±2% é calculada entre canais detectados e em relação ao valor transmitido, já limitado à faixa;
- canais não detectados aparecem no recall;
- séries saturadas não permitem recuperar o valor original fora da faixa;
- os critérios automáticos da qualificação OpenAQ são estação fixa, monitor de referência, leitura em 24 horas e licença vigente para uso comercial e redistribuição;
- a origem oficial das séries é conferida manualmente, não pelo script.

Essas mudanças corrigem parte relevante da comunicação pública identificada na auditoria. Elas não corrigem a ausência de idade máxima nos adaptadores nem a falta de associação por execução entre valor original e recuperado.

### 2.3 PR #56 — Zod e limites de coleções, ainda não incorporado

O [PR #56](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/pull/56) permanece aberto. Seu head auditado é [`4104f656eb2208da4def781448b3672b75857b7a`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/commit/4104f656eb2208da4def781448b3672b75857b7a). Ele propõe:

- atualizar Zod de 3.25.76 para 4.6.7;
- limitar `sensors` e `capabilities` a 64 itens e cada string a 120 caracteres;
- limitar os arrays OpenAQ de sensores a 200, licenças a 50 e últimas medições a 500;
- atualizar a assinatura de `z.record` para Zod 4;
- atualizar dependências transitivas `glob`, `minimatch` e `path-scurry` por override/lockfile.

No corte desta atualização, os jobs `api` e `docker-images` passaram, assim como Trivy e as análises CodeQL concluídas. Os checks de documentação, análise estática C++ e licença continuam falhando por problemas preexistentes descritos abaixo. Como o PR não está integrado, **Zod 3.25.76 e o achado HIGH permanecem no baseline `7ec77b6`**.

## 3. Novo achado de licença e copyright

### 3.1 Evidência

O arquivo [`LICENSE`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/7ec77b6d839588e49d87906f1d6d931ed419376a/LICENSE) começa com:

```text
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International Public License
Copyright (c) 2025 Guilherme Gonçalves Machado
```

Isso corresponde à licença Creative Commons Attribution–NonCommercial–ShareAlike 4.0 International (CC BY-NC-SA 4.0, Atribuição–NãoComercial–CompartilhaIgual). Entretanto:

- [`README.md`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/7ec77b6d839588e49d87906f1d6d931ed419376a/README.md) exibe badge e texto **CC BY 4.0**;
- [`README.pt.md`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/7ec77b6d839588e49d87906f1d6d931ed419376a/README.pt.md) também declara **CC BY 4.0**;
- o [`CHANGELOG.md`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/7ec77b6d839588e49d87906f1d6d931ed419376a/CHANGELOG.md) menciona a mudança para CC BY-NC-SA 4.0;
- o job de licença em [`.github/workflows/security.yml`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/7ec77b6d839588e49d87906f1d6d931ed419376a/.github/workflows/security.yml#L99-L126) procura corretamente o nome CC BY-NC-SA no `LICENSE`, mas exige `Copyright (c) 2024 Guilherme Gonçalves Machado` no README;
- o `LICENSE` usa o ano 2025 e o README não contém a expressão de 2024 esperada.

### 3.2 Consequência

CC BY 4.0 permite uso comercial; CC BY-NC-SA 4.0 proíbe uso comercial sem autorização adicional e exige compartilhamento de adaptações sob condições compatíveis. A divergência altera materialmente o direito anunciado aos usuários. Ela também mantém o workflow vermelho por uma expectativa de copyright que não corresponde ao arquivo normativo.

### 3.3 Prioridade

**Prioridade 0 (P0, necessária antes de novas alegações ou distribuição comercial):** o titular deve escolher conscientemente a licença do repositório, alinhar `LICENSE`, badges, READMEs, documentação, metadados dos depósitos e teste automatizado, além de definir o ano/nome de copyright canônico. Esta auditoria não decide qual licença deve ser escolhida.

## 4. Diagnóstico corrigido dos workflows

O baseline `7ec77b6` apresentou:

- [API CI 41663567516](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/actions/runs/41663567516): sucesso;
- [Deploy AWS 41664143351](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/actions/runs/41664143351): sucesso;
- [Continuous Integration 41663567447](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/actions/runs/41663567447): falha;
- [Security Checks 41663567391](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/actions/runs/41663567391): falha.

Continuous Integration (CI, integração contínua) e Security Checks falham por causas distintas. O diagnóstico correto é:

| Job | Causa observada | O que a falha não significa |
|---|---|---|
| TruffleHog | No evento `push` para `main`, o workflow configura `base: main` e `head: HEAD`; ambos resolvem para o mesmo commit. O log diz que não há intervalo para varrer. | Não significa que um segredo foi encontrado. |
| Trivy | A varredura produz o arquivo Static Analysis Results Interchange Format (SARIF, formato de intercâmbio de resultados de análise estática). A etapa de upload falha por falta de permissão para os endpoints do CodeQL/GitHub Security. | Não significa que o Trivy encontrou uma vulnerabilidade que derrubou o job. O Trivy da API e do PR #56 passou. |
| Markdownlint | Os READMEs existentes violam regras de comprimento de linha, blocos sem linguagem, URLs nuas e HTML inline. | Não indica falha de compilação ou do Nautam Live. |
| Cppcheck | `--enable=all --error-exitcode=1` transforma achados de estilo, incluindo funções não usadas de `SecureConfig`, em falha. | Não demonstra vulnerabilidade nem erro de runtime por si só. |
| Setup C++ com Clang | O action não conseguiu resolver `apt.llvm.org`, com `getaddrinfo EAI_AGAIN`. | É falha de rede/DNS (Domain Name System, sistema de nomes de domínio), não falha do compilador do projeto. |
| License Compliance Check | Procura copyright de 2024 inexistente, enquanto o `LICENSE` usa 2025. | Não significa ausência do arquivo `LICENSE`; revela teste desatualizado e divergência editorial. |

A consequência de engenharia permanece: checks permanentemente vermelhos dificultam distinguir regressão real de falha de configuração. A correção deve tornar cada job semanticamente útil, não apenas fazê-lo retornar zero.

## 5. Achados P1 do Nautam Live

### 5.1 Adaptadores sem idade máxima por leitura

O script de qualificação exige leitura OpenAQ nas últimas 24 horas, mas [`server/src/live/openaq.ts`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/7ec77b6d839588e49d87906f1d6d931ed419376a/server/src/live/openaq.ts) rejeita apenas timestamps inválidos ou mais de cinco minutos no futuro. Ele não rejeita leitura antiga.

[`server/src/live/ons.ts`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/7ec77b6d839588e49d87906f1d6d931ed419376a/server/src/live/ons.ts) também não aplica idade máxima. O endpoint público calcula “desatualizado” pelo horário de conclusão da execução, não pelo `observedAt` original.

**Consequência:** um job executado agora pode apresentar como atual uma observação antiga. A correção editorial do PR #55 reconhece que as fontes têm cadência própria, mas não corrige o estado calculado pela aplicação.

**Prioridade 1 (P1, próxima correção de validade do Live):** definir idade máxima por fonte/série; preservar observação antiga como histórica, mas impedir rótulo “ao vivo” quando o timestamp ultrapassar o limite.

### 5.2 Valor original e recuperado sem associação por `runId`

[`server/src/routes/live.ts`](https://github.com/guilherme-machado-ceo/iot-protocol-hubstry/blob/7ec77b6d839588e49d87906f1d6d931ed419376a/server/src/routes/live.ts) busca:

- a observação mais recente de cada série;
- separadamente, o run mais recente com protocolo;
- depois o navegador combina os dois por chave da série.

O schema contém `firstRunId`, mas sem relação Prisma/chave estrangeira, e o resumo não exige que a leitura exibida tenha participado do mesmo quadro que gerou o valor recuperado.

**Consequência:** sob falha parcial, nova coleta ou diferença entre runs, as colunas “original” e “recuperado” podem representar execuções distintas.

**P1:** retornar e consultar observações vinculadas ao run do protocolo exibido; incluir `runId`/slot no contrato público e testar deliberadamente dois runs divergentes.

## 6. Janela coerente e algoritmo de Goertzel

O receptor HPM conhece antecipadamente apenas 12 frequências. Ele não precisa calcular todo o espectro para recuperar esses canais.

A janela coerente mínima tem 480 amostras a 131.072 amostras/s. Embora 480 não seja potência de dois, isso não obriga a usar a Transformada Rápida de Fourier (Fast Fourier Transform, FFT) de tamanho misto nem o fallback quadrático atual. O **algoritmo de Goertzel** calcula coeficientes selecionados da Transformada Discreta de Fourier (Discrete Fourier Transform, DFT) diretamente nas frequências conhecidas, com custo aproximado proporcional a `K×N`, onde `K=12` e `N=480`.

Para esse caso:

```text
Goertzel: aproximadamente 12 × 480 atualizações
DFT completa ingênua: proporcional a 480²
FFT mista: possível, mas desnecessária para apenas 12 bins conhecidos
```

Isso torna a janela de 480 amostras uma opção tecnicamente simples para o receptor conhecido. O decodificador cego, que procura picos fora da tabela, continua exigindo análise espectral mais ampla ou outra estratégia. Antes de substituir o algoritmo, deve-se comparar no mesmo conjunto de sinais:

- erro de amplitude;
- recall e precisão;
- sensibilidade a desvio de frequência;
- tempo de CPU;
- custo de memória;
- comportamento com fase e ruído.

## 7. Matriz de evidências e prioridades atualizada

| Prioridade | ID | Achado | Estado no baseline `7ec77b6` | Evidência | Condição de encerramento |
|---|---|---|---|---|---|
| **P0** | P0-H16 | Cardinalidade Python/README 80 versus conjunto implementado com 159; Omnigrid 160 versus 318. | Aberto | `cardinality_hn()`, HALE, README e teste TS; cálculo independente e revisão Luna. | Python, TypeScript e documentação usam uma definição e os mesmos valores, com teste analítico independente. |
| **P0** | P0-JANELA | Cinco canais HPM não são coerentes no quadro de 2.048 amostras. | Aberto | Offsets de 1/3 e 0,4 bin; correlação `0,0065`; janela de 480 em erro de máquina. | Janela coerente ou não ortogonalidade explicitamente modelada; comparação FFT/Goertzel com limites objetivos. |
| **P0** | P0-LICENCA | `LICENSE` é CC BY-NC-SA 4.0/2025; READMEs dizem CC BY 4.0; teste exige copyright 2024. | Novo, aberto | Arquivos no baseline e License Compliance Check. | Titular escolhe a licença; todos os textos, badges, metadados e testes ficam idênticos ao arquivo normativo. |
| **P0** | P0-ZOD | Zod 3.25.76 está vulnerável a consumo descontrolado em coleções; arrays sem limite existiam. | Aberto no `main`; mitigação proposta no PR #56 | `npm audit`, GHSA e diff do PR #56. | PR aprovado após API CI, testes de limite e `npm audit --omit=dev` sem HIGH aplicável. |
| **P1** | P1-IDADE | OpenAQ e ONS não impõem idade máxima no runtime; staleness usa fim do job. | Aberto | Adaptadores e `routes/live.ts`. | Testes com observações antigas mostram rótulo correto por fonte e idade original. |
| **P1** | P1-RUN | Endpoint não garante o mesmo `runId` entre original e recuperado. | Aberto | Consultas separadas no resumo e `firstRunId` sem relação. | API retorna pares do mesmo run; teste com runs divergentes não cruza valores. |
| **P1** | P1-WORKFLOWS | CI geral e Security Checks falham por configuração, lint/estilo e rede. | Aberto | Runs 41663567447 e 41663567391. | Um mesmo SHA passa checks significativos; teste proposital prova que cada job detecta sua classe de erro. |
| **P1** | P1-LOOPBACK | Não existe validação com relógios independentes, DAC/ADC ou canal físico. | Aberto | Ausência de captura física; simulação usa relógio perfeito e ruído sintético. | Loopback baseband registra amostras, clocks, desvio, canal, resultados e intervalos de confiança. |

## 8. Parecer mantido

### CONDITIONAL GO

Mantém-se **CONDITIONAL GO** para um experimento físico de baixo custo, preferencialmente loopback de baseband com conversor digital-analógico e conversor analógico-digital de relógios independentes, comparando a janela atual com 480 amostras e o receptor FFT com Goertzel.

Mantém-se **NO-GO** para alegar:

- protocolo físico maduro;
- interferência zero;
- economia energética;
- escalabilidade infinita;
- funcionamento em qualquer hardware;
- sincronização nativa sem mecanismo de aquisição;
- segurança intrínseca ou criptografia harmônica comprovada.

Os PRs #54 e #55 melhoraram a transparência do painel, mas não mudam a maturidade tecnológica. O PR #56 trata uma vulnerabilidade de dependência e limites de entrada, mas ainda não pertence ao baseline incorporado.

## 9. Próxima decisão recomendada

A ordem de menor risco e maior evidência é:

1. resolver H16, janela, licença e Zod como P0;
2. corrigir idade e correspondência por run do Live;
3. restaurar workflows com significado verificável;
4. executar loopback de baseband com clocks independentes;
5. decidir sobre Software-Defined Radio (SDR, rádio definido por software) somente se o loopback demonstrar recuperação estável e uma vantagem mensurável da grade HPM.

Conteúdo externo foi resumido e reformulado para conformidade com restrições de licenciamento.