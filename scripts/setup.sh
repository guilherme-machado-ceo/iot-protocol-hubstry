#!/bin/bash

# Harmonic IoT Protocol - Development Environment Setup Script
# Copyright (c) 2024 Guilherme Gonçalves Machado
# Licensed under CC BY-NC-SA 4.0

set -e

echo "🎵 Harmonic IoT Protocol - Development Setup"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on supported OS
check_os() {
    print_status "Checking operating system..."

    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        print_success "Linux detected"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        print_success "macOS detected"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
        print_success "Windows detected"
    else
        print_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
}

# Install dependencies based on OS
install_dependencies() {
    print_status "Installing dependencies..."

    case $OS in
        "linux")
            if command -v apt-get &> /dev/null; then
                sudo apt-get update
                sudo apt-get install -y build-essential cmake git clang-format cppcheck valgrind gdb
            elif command -v yum &> /dev/null; then
                sudo yum groupinstall -y "Development Tools"
                sudo yum install -y cmake git clang-tools-extra cppcheck valgrind gdb
            else
                print_error "Unsupported Linux distribution"
                exit 1
            fi
            ;;
        "macos")
            if ! command -v brew &> /dev/null; then
                print_error "Homebrew not found. Please install Homebrew first."
                exit 1
            fi
            brew install cmake git clang-format cppcheck
            ;;
        "windows")
            print_warning "Windows setup requires manual installation of:"
            print_warning "- Visual Studio 2019/2022 with C++ tools"
            print_warning "- CMake"
            print_warning "- Git"
            ;;
    esac

    print_success "Dependencies installed"
}

# Check required tools
check_tools() {
    print_status "Checking required tools..."

    tools=("git" "cmake")

    for tool in "${tools[@]}"; do
        if command -v $tool &> /dev/null; then
            version=$($tool --version | head -n1)
            print_success "$tool found: $version"
        else
            print_error "$tool not found"
            exit 1
        fi
    done

    # Check C++ compiler
    if command -v g++ &> /dev/null; then
        version=$(g++ --version | head -n1)
        print_success "g++ found: $version"
    elif command -v clang++ &> /dev/null; then
        version=$(clang++ --version | head -n1)
        print_success "clang++ found: $version"
    else
        print_error "No C++ compiler found"
        exit 1
    fi
}

# Setup project structure
setup_project() {
    print_status "Setting up project structure..."

    # Create build directory
    if [ ! -d "src/build" ]; then
        mkdir -p src/build
        print_success "Created build directory"
    fi

    # Initialize git hooks if in git repository
    if [ -d ".git" ]; then
        print_status "Setting up git hooks..."

        # Pre-commit hook for code formatting
        cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Format C++ files before commit
find src/ -name "*.cpp" -o -name "*.h" | xargs clang-format -i
git add -u
EOF
        chmod +x .git/hooks/pre-commit
        print_success "Git hooks configured"
    fi
}

# Build the project
build_project() {
    print_status "Building the project..."

    cd src/build

    # Configure with CMake
    cmake .. -DCMAKE_BUILD_TYPE=Debug

    # Build
    cmake --build . --config Debug

    cd ../..

    print_success "Project built successfully"
}

# Run tests
run_tests() {
    print_status "Running tests..."

    cd src/build

    if [ -f "harmonic_protocol" ] || [ -f "harmonic_protocol.exe" ]; then
        ./harmonic_protocol || true
        print_success "Tests completed"
    else
        print_warning "No test executable found"
    fi

    cd ../..
}

# Validate setup
validate_setup() {
    print_status "Validating setup..."

    # Check if build was successful
    if [ -d "src/build" ] && [ "$(ls -A src/build)" ]; then
        print_success "Build directory exists and is not empty"
    else
        print_error "Build validation failed"
        exit 1
    fi

    # Validate documentation
    if [ -f "README.md" ] && [ -f "README.pt.md" ]; then
        print_success "Bilingual documentation found"
    else
        print_error "Documentation validation failed"
        exit 1
    fi

    # Check license
    if [ -f "LICENSE" ]; then
        if grep -q "Creative Commons" LICENSE; then
            print_success "License validation passed"
        else
            print_error "License validation failed"
            exit 1
        fi
    else
        print_error "LICENSE file not found"
        exit 1
    fi
}

# Main setup function
main() {
    echo
    print_status "Starting Harmonic IoT Protocol development setup..."
    echo

    check_os
    install_dependencies
    check_tools
    setup_project
    build_project
    run_tests
    validate_setup

    echo
    print_success "🎵 Setup completed successfully!"
    echo
    print_status "Next steps:"
    echo "  1. Open the project in your favorite IDE"
    echo "  2. Read the documentation in docs/"
    echo "  3. Check out CONTRIBUTING.md for development guidelines"
    echo "  4. Start developing harmonic communication features!"
    echo
    print_status "Happy coding with harmonic frequencies! 🎼"
}

# Run main function
main "$@"
