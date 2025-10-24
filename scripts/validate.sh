#!/bin/bash

# Harmonic IoT Protocol - Documentation Validation Script
# Copyright (c) 2024 Guilherme Gonçalves Machado
# Licensed under CC BY-NC-SA 4.0

set -e

echo "🎵 Harmonic IoT Protocol - Documentation Validation"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED_CHECKS++))
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED_CHECKS++))
}

increment_total() {
    ((TOTAL_CHECKS++))
}

# Check if file exists
check_file_exists() {
    local file=$1
    local description=$2

    increment_total
    if [ -f "$file" ]; then
        print_success "$description exists: $file"
        return 0
    else
        print_error "$description missing: $file"
        return 1
    fi
}

# Check bilingual documentation consistency
check_bilingual_consistency() {
    print_status "Checking bilingual documentation consistency..."

    # Check README files
    increment_total
    if [ -f "README.md" ] && [ -f "README.pt.md" ]; then
        # Check if both files have similar structure
        en_sections=$(grep -c "^##" README.md || echo 0)
        pt_sections=$(grep -c "^##" README.pt.md || echo 0)

        if [ "$en_sections" -eq "$pt_sections" ]; then
            print_success "README files have consistent structure ($en_sections sections each)"
        else
            print_error "README files have inconsistent structure (EN: $en_sections, PT: $pt_sections sections)"
        fi
    else
        print_error "Missing bilingual README files"
    fi

    # Check CONTRIBUTING files
    increment_total
    if [ -f "CONTRIBUTING.md" ] && [ -f "CONTRIBUTING.pt.md" ]; then
        print_success "Bilingual CONTRIBUTING files exist"
    else
        print_error "Missing bilingual CONTRIBUTING files"
    fi

    # Check documentation directories
    increment_total
    if [ -d "docs/en" ] && [ -d "docs/pt" ]; then
        en_docs=$(find docs/en -name "*.md" | wc -l)
        pt_docs=$(find docs/pt -name "*.md" | wc -l)

        if [ "$en_docs" -eq "$pt_docs" ]; then
            print_success "Documentation directories have consistent file count ($en_docs files each)"
        else
            print_error "Documentation directories have inconsistent file count (EN: $en_docs, PT: $pt_docs)"
        fi
    else
        print_error "Missing bilingual documentation directories"
    fi
}

# Validate markdown syntax
validate_markdown() {
    print_status "Validating markdown syntax..."

    # Find all markdown files
    markdown_files=$(find . -name "*.md" -not -path "./node_modules/*" -not -path "./.git/*")

    for file in $markdown_files; do
        increment_total

        # Check for basic markdown issues
        if grep -q "^#[^# ]" "$file"; then
            # Check for proper heading format
            if grep -q "^# " "$file"; then
                print_success "Markdown syntax valid: $file"
            else
                print_error "Invalid heading format in: $file"
            fi
        else
            print_warning "No main heading found in: $file"
        fi
    done
}

# Check license compliance
check_license_compliance() {
    print_status "Checking license compliance..."

    # Check LICENSE file
    increment_total
    if [ -f "LICENSE" ]; then
        if grep -q "Creative Commons Attribution-NonCommercial-ShareAlike 4.0" LICENSE; then
            print_success "LICENSE file contains correct CC BY-NC-SA 4.0 text"
        else
            print_error "LICENSE file does not contain CC BY-NC-SA 4.0 license"
        fi
    else
        print_error "LICENSE file not found"
    fi

    # Check copyright notices
    increment_total
    if grep -q "Copyright (c) 2024 Guilherme Gonçalves Machado" README.md; then
        print_success "Copyright notice found in README.md"
    else
        print_error "Copyright notice missing in README.md"
    fi

    increment_total
    if grep -q "Guilherme Gonçalves Machado" README.pt.md; then
        print_success "Copyright notice found in README.pt.md"
    else
        print_error "Copyright notice missing in README.pt.md"
    fi
}

# Validate links
validate_links() {
    print_status "Validating internal links..."

    # Check for broken internal links in README files
    for readme in README.md README.pt.md; do
        if [ -f "$readme" ]; then
            increment_total

            # Extract markdown links
            links=$(grep -o '\[.*\]([^)]*\.md[^)]*)' "$readme" | sed 's/.*(\([^)]*\)).*/\1/' || echo "")

            broken_links=0
            for link in $links; do
                # Skip external links
                if [[ $link == http* ]]; then
                    continue
                fi

                # Check if file exists
                if [ ! -f "$link" ]; then
                    print_warning "Broken link in $readme: $link"
                    ((broken_links++))
                fi
            done

            if [ $broken_links -eq 0 ]; then
                print_success "All internal links valid in $readme"
            else
                print_error "$broken_links broken internal links found in $readme"
            fi
        fi
    done
}

# Check project structure
check_project_structure() {
    print_status "Checking project structure..."

    # Required files
    required_files=(
        "README.md"
        "README.pt.md"
        "LICENSE"
        "CONTRIBUTING.md"
        "CONTRIBUTING.pt.md"
        "CODE_OF_CONDUCT.md"
        "CHANGELOG.md"
        ".gitignore"
    )

    for file in "${required_files[@]}"; do
        check_file_exists "$file" "Required file"
    done

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

    for dir in "${required_dirs[@]}"; do
        increment_total
        if [ -d "$dir" ]; then
            print_success "Required directory exists: $dir"
        else
            print_error "Required directory missing: $dir"
        fi
    done
}

# Validate GitHub templates
validate_github_templates() {
    print_status "Validating GitHub templates..."

    # Issue templates
    templates=(
        ".github/ISSUE_TEMPLATE/bug_report.md"
        ".github/ISSUE_TEMPLATE/feature_request.md"
        ".github/ISSUE_TEMPLATE/question.md"
        ".github/PULL_REQUEST_TEMPLATE.md"
    )

    for template in "${templates[@]}"; do
        check_file_exists "$template" "GitHub template"
    done

    # Workflow files
    workflows=(
        ".github/workflows/ci.yml"
        ".github/workflows/release.yml"
        ".github/workflows/security.yml"
    )

    for workflow in "${workflows[@]}"; do
        check_file_exists "$workflow" "GitHub workflow"
    done
}

# Check harmonic protocol specific content
check_harmonic_content() {
    print_status "Checking harmonic protocol specific content..."

    # Check for harmonic-related terms in documentation
    harmonic_terms=("harmonic" "frequency" "f₀" "FFT" "spectral")

    for term in "${harmonic_terms[@]}"; do
        increment_total
        if grep -qi "$term" README.md; then
            print_success "Harmonic term '$term' found in documentation"
        else
            print_warning "Harmonic term '$term' not found in documentation"
        fi
    done

    # Check for mathematical symbols
    increment_total
    if grep -q "f₀" README.md; then
        print_success "Mathematical notation (f₀) found in documentation"
    else
        print_error "Mathematical notation missing in documentation"
    fi
}

# Generate validation report
generate_report() {
    echo
    echo "🎵 Validation Report"
    echo "==================="
    echo "Total checks: $TOTAL_CHECKS"
    echo -e "Passed: ${GREEN}$PASSED_CHECKS${NC}"
    echo -e "Failed: ${RED}$FAILED_CHECKS${NC}"
    echo

    if [ $FAILED_CHECKS -eq 0 ]; then
        print_success "All validation checks passed! 🎉"
        echo "Your Harmonic IoT Protocol repository is ready for collaboration."
        return 0
    else
        print_error "Some validation checks failed."
        echo "Please address the issues above before proceeding."
        return 1
    fi
}

# Main validation function
main() {
    echo
    print_status "Starting documentation validation..."
    echo

    check_project_structure
    check_bilingual_consistency
    validate_markdown
    check_license_compliance
    validate_links
    validate_github_templates
    check_harmonic_content

    generate_report
}

# Run main function
main "$@"
