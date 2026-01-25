# Everruns SDK - Task automation

default:
    @just --list

# Setup all SDKs
setup:
    cd rust && cargo build
    cd python && uv sync --all-extras
    cd typescript && npm ci

# Run all tests
test: test-rust test-python test-typescript

# Test Rust SDK
test-rust:
    cd rust && cargo test

# Test Python SDK  
test-python:
    cd python && uv run pytest

# Test TypeScript SDK
test-typescript:
    cd typescript && npm test

# Lint all SDKs
lint: lint-rust lint-python lint-typescript

# Lint Rust
lint-rust:
    cd rust && cargo fmt --check
    cd rust && cargo clippy -- -D warnings

# Lint Python
lint-python:
    cd python && uv run ruff check .
    cd python && uv run ruff format --check .

# Lint TypeScript
lint-typescript:
    cd typescript && npm run lint

# Generate types from OpenAPI spec
generate:
    cd rust && cargo build
    cd python && datamodel-codegen --input ../openapi/openapi.json --output everruns_sdk/_generated/models.py
    cd typescript && npx openapi-typescript ../openapi/openapi.json -o src/generated/schema.d.ts

# Run coverage for all SDKs
coverage:
    cd rust && cargo llvm-cov --lcov --output-path lcov.info
    cd python && uv run pytest --cov=everruns_sdk --cov-report=xml
    cd typescript && npm test -- --coverage

# Pre-PR checks
pre-pr: lint test
    @echo "All checks passed!"

# Dry-run publish
publish-dry-run:
    cd rust && cargo publish --dry-run
    cd python && uv build
    cd typescript && npm run build

# Check Rust cookbooks compile
check-cookbooks:
    cd cookbook/rust && cargo check --all

# Lint Rust cookbooks
lint-cookbooks:
    cd cookbook/rust && cargo fmt --check --all
    cd cookbook/rust && cargo clippy --all -- -D warnings

# Format Rust cookbooks
fmt-cookbooks:
    cd cookbook/rust && cargo fmt --all

# Run a specific cookbook (requires env vars: EVERRUNS_ORG, EVERRUNS_API_KEY)
run-cookbook name:
    cd cookbook/rust && cargo run -p {{name}}
