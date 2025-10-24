# Contributing to Harmonic IoT Protocol

[![Language: PT](https://img.shields.io/badge/lang-PT-green.svg)](CONTRIBUTING.pt.md) | **EN**

Thank you for your interest in contributing to the Harmonic IoT Protocol! This document provides guidelines for contributing to this innovative communication protocol project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Process](#development-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Community](#community)

## 📜 Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to guilherme.ceo@hubstry.com.

## 🚀 Getting Started

### Prerequisites

- C++ compiler (GCC, Clang, or MSVC)
- CMake 3.10 or higher
- Git for version control
- Basic understanding of IoT protocols and signal processing

### Setting Up Development Environment

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/harmonic-iot-protocol.git
   cd harmonic-iot-protocol
   ```

2. **Build the project**
   ```bash
   cd src
   mkdir build && cd build
   cmake ..
   make
   ```

3. **Run tests**
   ```bash
   ./harmonic_protocol
   ```

## 🤝 How to Contribute

### Reporting Issues

Before creating an issue, please:

1. **Search existing issues** to avoid duplicates
2. **Use the issue templates** provided
3. **Provide detailed information** including:
   - Operating system and version
   - Compiler version
   - Steps to reproduce
   - Expected vs actual behavior
   - Relevant logs or error messages

### Suggesting Enhancements

Enhancement suggestions are welcome! Please:

1. **Use the feature request template**
2. **Explain the use case** and benefits
3. **Consider the mathematical foundations** of the harmonic protocol
4. **Discuss implementation feasibility**

### Contributing Code

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow coding standards
   - Add tests for new functionality
   - Update documentation as needed

3. **Commit your changes**
   ```bash
   git commit -m "feat: add harmonic channel validation"
   ```

4. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**
   - Use the PR template
   - Link related issues
   - Provide clear description of changes

## 🔄 Development Process

### Branch Strategy

- `main`: Stable release branch
- `develop`: Integration branch for new features
- `feature/*`: Feature development branches
- `hotfix/*`: Critical bug fixes

### Commit Message Convention

We follow the [Conventional Commits](https://conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(harmonic): add frequency validation for f₀
fix(gateway): resolve FFT memory leak
docs(readme): update installation instructions
```

## 💻 Coding Standards

### C++ Guidelines

- **Follow C++17 standards**
- **Use meaningful variable names**
- **Comment complex algorithms**, especially harmonic calculations
- **Include header guards** in all header files
- **Use const correctness**
- **Prefer RAII** for resource management

### Code Style

```cpp
// Good: Clear naming and documentation
class HarmonicChannel {
private:
    double fundamental_frequency_;  // f₀ in Hz
    int harmonic_number_;          // n in Hn = n * f₀
    
public:
    /**
     * @brief Calculate the harmonic frequency
     * @return The frequency of this harmonic channel (Hn * f₀)
     */
    double getFrequency() const {
        return harmonic_number_ * fundamental_frequency_;
    }
};
```

### Documentation Standards

- **Document all public APIs**
- **Include mathematical formulas** where relevant
- **Provide usage examples**
- **Explain harmonic protocol concepts**

## 🧪 Testing Guidelines

### Test Requirements

- **Unit tests** for all new functions
- **Integration tests** for protocol features
- **Performance tests** for critical paths
- **Documentation tests** for examples

### Test Structure

```cpp
#include <gtest/gtest.h>
#include "harmonic_channel.h"

class HarmonicChannelTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Test setup
    }
};

TEST_F(HarmonicChannelTest, CalculatesCorrectFrequency) {
    HarmonicChannel channel(1000.0, 3);  // f₀=1kHz, H3
    EXPECT_DOUBLE_EQ(channel.getFrequency(), 3000.0);
}
```

## 📚 Documentation

### Documentation Types

1. **API Documentation**: In-code comments and headers
2. **User Guides**: Step-by-step tutorials
3. **Technical Specifications**: Mathematical foundations
4. **Examples**: Working code samples

### Bilingual Documentation

- **English**: Primary language for technical documentation
- **Portuguese**: Secondary language for accessibility
- **Maintain consistency** between language versions
- **Update both versions** when making changes

## 🌍 Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Email**: guilherme.ceo@hubstry.com for partnership inquiries

### Getting Help

1. **Check existing documentation** first
2. **Search closed issues** for similar problems
3. **Ask in GitHub Discussions** for general questions
4. **Create an issue** for bugs or specific problems

### Recognition

Contributors will be recognized in:
- **CONTRIBUTORS.md** file
- **Release notes** for significant contributions
- **Project documentation** for major features

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the [CC BY-NC-SA 4.0](LICENSE) license.

## 🙏 Acknowledgments

We appreciate all contributions, whether they're:
- Code improvements
- Bug reports
- Documentation enhancements
- Feature suggestions
- Community support

Thank you for helping make the Harmonic IoT Protocol better!

---

**Questions?** Feel free to reach out via GitHub issues or email: guilherme.ceo@hubstry.com