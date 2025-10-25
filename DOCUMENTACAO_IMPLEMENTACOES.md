# Documentação de Implementações Recentes

Este documento detalha as principais funcionalidades e alterações técnicas implementadas no sistema, com foco nas melhorias de segurança e visualização de dados.

## 1. Camada de Segurança Híbrida com Criptografia Pós-Quântica (PQC)

Para proteger o sistema contra ameaças futuras de computadores quânticos, foi implementada uma camada de segurança híbrida. Esta abordagem combina a robustez da criptografia clássica (já existente) com algoritmos de Criptografia Pós-Quântica (PQC) para dados de alta sensibilidade.

### Detalhes da Implementação:

- **Abordagem Híbrida:** A autenticação primária do sistema foi mantida com os protocolos clássicos, garantindo harmonia e compatibilidade. A criptografia PQC foi adicionada como uma camada extra de segurança, especificamente para a proteção de *payloads* de dados sensíveis, como credenciais de usuário.

- **Algoritmos PQC Utilizados:**
  - **Kyber (CRYSTALS-Kyber):** Utilizado para o Mecanismo de Encapsulamento de Chave (KEM). Gera um segredo compartilhado para criptografar o *payload*.
  - **Dilithium (CRYSTALS-Dilithium):** Utilizado para a geração de assinaturas digitais, garantindo a autenticidade e a integridade da mensagem.
  - Ambos os algoritmos foram escolhidos por serem padrões finalistas do **NIST PQC Standardization Process**.

- **Integração Técnica (Backend - C++):**
  - A biblioteca **`liboqs`** (Open Quantum Safe) foi integrada ao backend para fornecer as implementações dos algoritmos PQC.
  - A classe `SecureConfig` (em `src/security/`) foi estendida para incluir os novos métodos de criptografia:
    - `pqcKeygen()`: Geração de pares de chaves PQC.
    - `pqcEncaps()` / `pqcDecaps()`: Funções para encapsulamento e desencapsulamento de chave (Kyber).
    - `pqcSign()` / `pqcVerify()`: Funções para assinar e verificar mensagens (Dilithium).

- **Protocolo Estendido:** Os protocolos de comunicação (similares a MQTT/CoAP) foram estendidos para suportar a nova camada de segurança, incluindo cabeçalhos para verificação harmônica e um *payload* criptografado com PQC.

## 2. Dashboard de Métricas de Segurança PQC

Para monitorar a saúde e a eficácia da nova camada de segurança, o dashboard da aplicação web foi atualizado para incluir métricas específicas de PQC.

### Detalhes da Implementação:

- **Novas Métricas Adicionadas:**
  - **"Taxa de Assinaturas Inválidas":** Exibe a porcentagem de assinaturas digitais que falharam na verificação. Um valor alto pode indicar tentativas de ataque ou problemas de integridade.
  - **"Uso de Chaves Kyber por Dispositivo":** Monitora a frequência de utilização do encapsulamento de chave Kyber, ajudando a identificar padrões de comunicação e dispositivos ativos.

- **Integração Técnica (Frontend - Next.js):**
  - O componente React `ProtocolMetrics.tsx` (em `demo-web/harmonic-demo/src/components/`) foi modificado para incluir os novos *cards* de métricas.
  - **Estado Atual:** No momento, os dados exibidos no dashboard são **simulados**, pois o backend ainda está em fase de finalização e integração completa. A lógica para gerar e consumir dados reais será implementada futuramente.
