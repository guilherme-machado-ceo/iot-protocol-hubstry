**PT** | [![Language: EN](https://img.shields.io/badge/lang-EN-blue.svg)](../en/Tests.md)

# Protocolo IoT Harmônico - Casos de Teste

Este documento descreve os casos de teste para o Protocolo IoT Harmônico baseado no Documento de Requisitos do Produto (PRD) aprovado.

## 1. Casos de Teste Funcionais

| ID do Caso de Teste | ID do Requisito | Cenário de Teste | Passos do Teste | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| TC-FR-001 | RF1 | Verificar Sincronização da Frequência Fundamental (f₀) | 1. Designar um nó como Mestre. <br> 2. Configurar o Mestre para transmitir f₀ = 1 kHz. <br> 3. Ligar três nós Escravos. <br> 4. Consultar a frequência sincronizada de cada nó Escravo. | Todos os três nós Escravos reportam uma frequência sincronizada de 1 kHz dentro de uma tolerância de +/- 0,1%. |
| TC-FR-002 | RF2 | Verificar Mapeamento de Canal Harmônico para Função | 1. Configurar a rede com f₀ = 1kHz. <br> 2. Mapear H2 (2kHz) para "read_temperature" no Dispositivo A. <br> 3. Mapear H3 (3kHz) para "toggle_led" no Dispositivo B. <br> 4. Enviar um comando genérico "read" em H3. <br> 5. Enviar um comando "toggle" em H2. | Dispositivo B (LED) não responde. Dispositivo A (temp) não responde. O sistema isola corretamente as funções para suas harmônicas mapeadas. |
| TC-FR-003 | RF3 & RF4 | Testar Codificação e Decodificação Harmônica Fim-a-Fim | 1. Configurar rede com f₀ = 1kHz. <br> 2. Atribuir Dispositivo A para H4 (4kHz). <br> 3. Instruir Dispositivo A a transmitir o valor "123". <br> 4. Um nó Gateway escuta todo o tráfego harmônico. | O Gateway isola corretamente o sinal em H4 e decodifica o payload como "123". Nenhum dado é detectado em outras harmônicas do Dispositivo A. |
| TC-FR-004 | RF5 | Verificar Roteamento Omnicanal | 1. Um sensor LoRa (Dispositivo L) está em H5. Um atuador Wi-Fi (Dispositivo W) está em H10. <br> 2. Dispositivo L transmite dados do sensor em H5. <br> 3. Configurar o Gateway para rotear qualquer dado de H5 para H10. | O Gateway recebe a transmissão LoRa em H5, decodifica, recodifica e transmite para o Dispositivo W via Wi-Fi em H10. |
| TC-FR-005 | RF6 | Testar Autenticação por Assinatura Harmônica | 1. Definir a assinatura do Dispositivo A como uma transmissão simultânea em H2 e H7. <br> 2. Dispositivo A transmite um payload válido em H2 e H7. <br> 3. Um Dispositivo B malicioso tenta transmitir apenas em H2. | O Gateway aceita a transmissão do Dispositivo A. O Gateway rejeita ou sinaliza a transmissão do Dispositivo B como "não autenticada". |
| TC-FR-006 | RF7 | Testar Detecção de Intrusão Espectral | 1. Estabelecer uma rede válida usando H2, H3 e H4. <br> 2. Introduzir um transmissor malicioso transmitindo um sinal forte em H5 (um canal não atribuído). | O sistema de monitoramento do Gateway imediatamente sinaliza um "Evento Espectral Não Autorizado" na frequência 5 * f₀. |

## 2. Casos de Teste Não-Funcionais

| ID do Caso de Teste | ID do Requisito | Cenário de Teste | Passos do Teste | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| TC-NFR-001 | RNF1 | Testar Robustez Contra Interferência | 1. Configurar um link de comunicação em H3 (3kHz). <br> 2. Introduzir um sinal RF interferente conhecido em 3,1 kHz. <br> 3. Transmitir 10.000 pacotes. | A Taxa de Erro de Bit (BER) permanece abaixo do limiar aceitável especificado (ex: < 10^-5), demonstrando a capacidade do protocolo de rejeitar ruído de frequência adjacente. |
| TC-NFR-002 | RNF2 | Testar Escalabilidade de Canais Harmônicos | 1. Configurar uma rede e simular a adição de dispositivos em 1.000 canais harmônicos diferentes. <br> 2. Comandar uma transmissão de um dispositivo em H999. | O sistema processa com sucesso a transmissão em H999 sem aumento significativo na latência ou carga de processamento no gateway. |
| TC-NFR-003 | RNF3 | Medir Latência em Tempo Real | 1. Disparar um evento de sensor no Dispositivo A. <br> 2. Medir o tempo do disparo até a recepção e decodificação bem-sucedida dos dados no Gateway. | A latência total fim-a-fim é menor que 50ms. |

## 3. Casos de Teste de Implementação

| ID do Caso de Teste | ID do Requisito | Cenário de Teste | Passos do Teste | Resultado Esperado |
| :--- | :--- | :--- | :--- | :--- |
| TC-IMP-001 | ED1 | Verificar Compilação do Protótipo C++ | 1. Navegar para o diretório `src/`. <br> 2. Executar o comando de build (ex: `make` ou `g++`). | O código do protótipo C++ compila com sucesso sem erros ou avisos. |