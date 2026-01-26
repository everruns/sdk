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

# Check cookbook compiles
check-cookbook:
    cd cookbook/rust && cargo check

# Lint cookbook
lint-cookbook:
    cd cookbook/rust && cargo fmt --check && cargo clippy -- -D warnings

# Run cookbook (requires EVERRUNS_API_KEY, EVERRUNS_API_URL)
run-cookbook:
    cd cookbook/rust && cargo run
