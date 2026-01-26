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

# Check all cookbooks compile
check-cookbook: check-cookbook-rust check-cookbook-python check-cookbook-typescript

# Check Rust cookbook
check-cookbook-rust:
    cd cookbook/rust && cargo check

# Check Python cookbook
check-cookbook-python:
    cd cookbook/python && uv sync
    cd cookbook/python && uv run python -m py_compile src/main.py

# Check TypeScript cookbook
check-cookbook-typescript:
    cd typescript && npm run build
    cd cookbook/typescript && npm install
    cd cookbook/typescript && npm run check

# Lint all cookbooks
lint-cookbook: lint-cookbook-rust lint-cookbook-python lint-cookbook-typescript

# Lint Rust cookbook
lint-cookbook-rust:
    cd cookbook/rust && cargo fmt --check && cargo clippy -- -D warnings

# Lint Python cookbook
lint-cookbook-python:
    cd cookbook/python && uv sync
    cd cookbook/python && uv run ruff check . && uv run ruff format --check .

# Lint TypeScript cookbook
lint-cookbook-typescript:
    cd cookbook/typescript && npm install
    cd cookbook/typescript && npm run lint

# Run Rust cookbook (requires EVERRUNS_API_KEY, EVERRUNS_API_URL)
run-cookbook-rust:
    cd cookbook/rust && cargo run

# Run Python cookbook (requires EVERRUNS_API_KEY, EVERRUNS_API_URL)
run-cookbook-python:
    cd cookbook/python && uv run python src/main.py

# Run TypeScript cookbook (requires EVERRUNS_API_KEY, EVERRUNS_API_URL)
run-cookbook-typescript:
    cd cookbook/typescript && npx tsx src/main.ts
