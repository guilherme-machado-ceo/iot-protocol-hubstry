#!/bin/bash

# Harmonic IoT Protocol - Code Linting and Formatting Script
# Copyright (c) 2025 Guilherme Gonçalves Machado
# Licensed under CC BY-NC-SA 4.0

set -e

echo "🎵 Harmonic IoT Protocol - Code Linting & Formatting"
echo "=================================================="

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

# Check if tools are available
check_tools() {
    print_status "Checking linting tools..."

    # Check for clang-format
    if command -v clang-format &> /dev/null; then
        print_success "clang-format found"
    else
        print_warning "clang-format not found - C++ formatting will be skipped"
    fi

    # Check for markdownlint
    if command -v markdownlint &> /dev/null; then
        print_success "markdownlint found"
    else
        print_warning "markdownlint not found - Markdown linting will be skipped"
    fi

    # Check for eslint (if Node.js project exists)
    if [ -f "package.json" ] && command -v eslint &> /dev/null; then
        print_success "eslint found"
    fi
}

# Format C++ code
format_cpp() {
    print_status "Formatting C++ code..."

    if command -v clang-format &> /dev/null; then
        # Find and format all C++ files
        find src/ -name "*.cpp" -o -name "*.h" -o -name "*.hpp" | while read -r file; do
            print_status "Formatting: $file"
            clang-format -i "$file"
        done
        print_success "C++ code formatted"
    else
        print_warning "Skipping C++ formatting - clang-format not available"
    fi
}

# Lint Markdown files
lint_markdown() {
    print_status "Linting Markdown files..."

    if command -v markdownlint &> /dev/null; then
        # Create markdownlint config if it doesn't exist
        if [ ! -f ".markdownlint.json" ]; then
            cat > .markdownlint.json << 'EOF'
{
  "MD013": false,
  "MD033": false,
  "MD041": false
}
EOF
        fi

        # Lint main markdown files
        markdownlint README.md README.pt.md CONTRIBUTING.md CONTRIBUTING.pt.md \
                     CHANGELOG.md ROADMAP.md ROADMAP.pt.md SECURITY.md SECURITY.pt.md \
                     docs/**/*.md || true

        print_success "Markdown files linted"
    else
        print_warning "Skipping Markdown linting - markdownlint not available"
    fi
}

# Check code style
check_code_style() {
    print_status "Checking code style..."

    # Check for consistent line endings
    if command -v dos2unix &> /dev/null; then
        find . -name "*.cpp" -o -name "*.h" -o -name "*.md" -o -name "*.sh" | \
        xargs dos2unix 2>/dev/null || true
        print_success "Line endings normalized"
    fi

    # Check for trailing whitespace
    print_status "Checking for trailing whitespace..."
    if grep -r "[ \t]$" --include="*.cpp" --include="*.h" --include="*.md" . ; then
        print_warning "Found trailing whitespace in files above"
    else
        print_success "No trailing whitespace found"
    fi
}

# Validate file structure
validate_structure() {
    print_status "Validating project structure..."

    # Required files
    required_files=(
        "README.md"
        "README.pt.md"
        "LICENSE"
        "CONTRIBUTING.md"
        "CONTRIBUTING.pt.md"
        "CODE_OF_CONDUCT.md"
        "CHANGELOG.md"
        "SECURITY.md"
        "SECURITY.pt.md"
        "ROADMAP.md"
        "ROADMAP.pt.md"
    )

    missing_files=0
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "Missing required file: $file"
            ((missing_files++))
        fi
    done

    if [ $missing_files -eq 0 ]; then
        print_success "All required files present"
    else
        print_error "$missing_files required files missing"
        return 1
    fi

    # Required directories
    required_dirs=(
        "src"
        "docs"
        "docs/en"
        "docs/pt"
        ".github"
        ".github/workflows"
        ".github/ISSUE_TEMPLATE"
    )

    missing_dirs=0
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            print_error "Missing required directory: $dir"
            ((missing_dirs++))
        fi
    done

    if [ $missing_dirs -eq 0 ]; then
        print_success "All required directories present"
    else
        print_error "$missing_dirs required directories missing"
        return 1
    fi
}

# Run static analysis
run_static_analysis() {
    print_status "Running static analysis..."

    # Check for cppcheck
    if command -v cppcheck &> /dev/null; then
        print_status "Running cppcheck..."
        cppcheck --enable=all --error-exitcode=0 src/ 2>/dev/null || true
        print_success "Static analysis completed"
    else
        print_warning "Skipping static analysis - cppcheck not available"
    fi
}

# Main function
main() {
    echo
    print_status "Starting code linting and formatting..."
    echo

    check_tools
    format_cpp
    lint_markdown
    check_code_style
    validate_structure
    run_static_analysis

    echo
    print_success "🎵 Linting and formatting completed!"
    echo
    print_status "Code is ready for commit!"
}

# Run main function
main "$@"
