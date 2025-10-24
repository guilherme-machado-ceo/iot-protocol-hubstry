# Contribuindo para o Protocolo IoT Harmônico

**PT** | [![Language: EN](https://img.shields.io/badge/lang-EN-blue.svg)](CONTRIBUTING.md)

Obrigado pelo seu interesse em contribuir para o Protocolo IoT Harmônico! Este documento fornece diretrizes para contribuir com este projeto inovador de protocolo de comunicação.

## 📋 Índice

- [Código de Conduta](#código-de-conduta)
- [Primeiros Passos](#primeiros-passos)
- [Como Contribuir](#como-contribuir)
- [Processo de Desenvolvimento](#processo-de-desenvolvimento)
- [Padrões de Código](#padrões-de-código)
- [Diretrizes de Teste](#diretrizes-de-teste)
- [Documentação](#documentação)
- [Comunidade](#comunidade)

## 📜 Código de Conduta

Este projeto adere ao [Código de Conduta do Contributor Covenant](CODE_OF_CONDUCT.md). Ao participar, espera-se que você mantenha este código. Por favor, reporte comportamentos inaceitáveis para guilherme.ceo@hubstry.com.

## 🚀 Primeiros Passos

### Pré-requisitos

- Compilador C++ (GCC, Clang ou MSVC)
- CMake 3.10 ou superior
- Git para controle de versão
- Entendimento básico de protocolos IoT e processamento de sinais

### Configurando o Ambiente de Desenvolvimento

1. **Faça um fork do repositório**
   ```bash
   git clone https://github.com/seu-usuario/harmonic-iot-protocol.git
   cd harmonic-iot-protocol
   ```

2. **Compile o projeto**
   ```bash
   cd src
   mkdir build && cd build
   cmake ..
   make
   ```

3. **Execute os testes**
   ```bash
   ./harmonic_protocol
   ```

## 🤝 Como Contribuir

### Reportando Problemas

Antes de criar um issue, por favor:

1. **Pesquise issues existentes** para evitar duplicatas
2. **Use os templates de issue** fornecidos
3. **Forneça informações detalhadas** incluindo:
   - Sistema operacional e versão
   - Versão do compilador
   - Passos para reproduzir
   - Comportamento esperado vs atual
   - Logs ou mensagens de erro relevantes

### Sugerindo Melhorias

Sugestões de melhorias são bem-vindas! Por favor:

1. **Use o template de solicitação de feature**
2. **Explique o caso de uso** e benefícios
3. **Considere as fundações matemáticas** do protocolo harmônico
4. **Discuta a viabilidade de implementação**

### Contribuindo com Código

1. **Crie uma branch de feature**
   ```bash
   git checkout -b feature/nome-da-sua-feature
   ```

2. **Faça suas alterações**
   - Siga os padrões de código
   - Adicione testes para nova funcionalidade
   - Atualize a documentação conforme necessário

3. **Commit suas alterações**
   ```bash
   git commit -m "feat: adicionar validação de canal harmônico"
   ```

4. **Push para seu fork**
   ```bash
   git push origin feature/nome-da-sua-feature
   ```

5. **Crie um Pull Request**
   - Use o template de PR
   - Vincule issues relacionados
   - Forneça descrição clara das alterações

## 🔄 Processo de Desenvolvimento

### Estratégia de Branches

- `main`: Branch de release estável
- `develop`: Branch de integração para novas features
- `feature/*`: Branches de desenvolvimento de features
- `hotfix/*`: Correções críticas de bugs

### Convenção de Mensagens de Commit

Seguimos a especificação [Conventional Commits](https://conventionalcommits.org/):

```
<tipo>[escopo opcional]: <descrição>

[corpo opcional]

[rodapé(s) opcional(is)]
```

**Tipos:**
- `feat`: Nova feature
- `fix`: Correção de bug
- `docs`: Alterações na documentação
- `style`: Alterações de estilo de código
- `refactor`: Refatoração de código
- `test`: Adicionando ou atualizando testes
- `chore`: Tarefas de manutenção

**Exemplos:**
```
feat(harmonic): adicionar validação de frequência para f₀
fix(gateway): resolver vazamento de memória no FFT
docs(readme): atualizar instruções de instalação
```

## 💻 Padrões de Código

### Diretrizes C++

- **Siga os padrões C++17**
- **Use nomes de variáveis significativos**
- **Comente algoritmos complexos**, especialmente cálculos harmônicos
- **Inclua header guards** em todos os arquivos de cabeçalho
- **Use const correctness**
- **Prefira RAII** para gerenciamento de recursos

### Estilo de Código

```cpp
// Bom: Nomenclatura clara e documentação
class CanalHarmonico {
private:
    double frequencia_fundamental_;  // f₀ em Hz
    int numero_harmonico_;          // n em Hn = n * f₀
    
public:
    /**
     * @brief Calcular a frequência harmônica
     * @return A frequência deste canal harmônico (Hn * f₀)
     */
    double obterFrequencia() const {
        return numero_harmonico_ * frequencia_fundamental_;
    }
};
```

### Padrões de Documentação

- **Documente todas as APIs públicas**
- **Inclua fórmulas matemáticas** onde relevante
- **Forneça exemplos de uso**
- **Explique conceitos do protocolo harmônico**

## 🧪 Diretrizes de Teste

### Requisitos de Teste

- **Testes unitários** para todas as novas funções
- **Testes de integração** para features do protocolo
- **Testes de performance** para caminhos críticos
- **Testes de documentação** para exemplos

### Estrutura de Teste

```cpp
#include <gtest/gtest.h>
#include "canal_harmonico.h"

class TesteCanalHarmonico : public ::testing::Test {
protected:
    void SetUp() override {
        // Configuração do teste
    }
};

TEST_F(TesteCanalHarmonico, CalculaFrequenciaCorreta) {
    CanalHarmonico canal(1000.0, 3);  // f₀=1kHz, H3
    EXPECT_DOUBLE_EQ(canal.obterFrequencia(), 3000.0);
}
```

## 📚 Documentação

### Tipos de Documentação

1. **Documentação de API**: Comentários no código e cabeçalhos
2. **Guias do Usuário**: Tutoriais passo a passo
3. **Especificações Técnicas**: Fundações matemáticas
4. **Exemplos**: Amostras de código funcionais

### Documentação Bilíngue

- **Inglês**: Idioma principal para documentação técnica
- **Português**: Idioma secundário para acessibilidade
- **Mantenha consistência** entre versões de idiomas
- **Atualize ambas as versões** ao fazer alterações

## 🌍 Comunidade

### Canais de Comunicação

- **GitHub Issues**: Relatórios de bugs e solicitações de features
- **GitHub Discussions**: Perguntas gerais e ideias
- **Email**: guilherme.ceo@hubstry.com para consultas de parceria

### Obtendo Ajuda

1. **Verifique a documentação existente** primeiro
2. **Pesquise issues fechados** para problemas similares
3. **Pergunte no GitHub Discussions** para questões gerais
4. **Crie um issue** para bugs ou problemas específicos

### Reconhecimento

Contribuidores serão reconhecidos em:
- Arquivo **CONTRIBUTORS.md**
- **Notas de release** para contribuições significativas
- **Documentação do projeto** para features principais

## 📄 Licença

Ao contribuir para este projeto, você concorda que suas contribuições serão licenciadas sob a licença [CC BY-NC-SA 4.0](LICENSE).

## 🙏 Agradecimentos

Apreciamos todas as contribuições, sejam elas:
- Melhorias de código
- Relatórios de bugs
- Melhorias na documentação
- Sugestões de features
- Suporte da comunidade

Obrigado por ajudar a tornar o Protocolo IoT Harmônico melhor!

---

**Dúvidas?** Sinta-se à vontade para entrar em contato via GitHub issues ou email: guilherme.ceo@hubstry.com