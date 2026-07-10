#!/usr/bin/env python3
"""Regenerate public SDK models from the local OpenAPI mirror."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence

from sdk_codegen import CodegenError, generate_public_models, load_config


REPO_ROOT = Path(__file__).resolve().parents[1]
OPENAPI_PATH = REPO_ROOT / "openapi" / "openapi.json"
UPSTREAM_OPENAPI_URL = (
    "https://raw.githubusercontent.com/everruns/everruns/main/docs/api/openapi.json"
)
TARGETS = ("rust", "python", "typescript")


class GenerationError(RuntimeError):
    """Raised when generation cannot proceed."""


def ensure_openapi_exists(openapi_path: Path = OPENAPI_PATH) -> None:
    if not openapi_path.is_file():
        raise GenerationError(f"missing OpenAPI spec: {openapi_path}")


def sync_openapi(openapi_path: Path = OPENAPI_PATH) -> None:
    openapi_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        with urllib.request.urlopen(UPSTREAM_OPENAPI_URL, timeout=30) as response:
            shutil.copyfileobj(response, tmp)

    try:
        json.loads(tmp_path.read_text())
        tmp_path.replace(openapi_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def expand_targets(targets: Iterable[str]) -> List[str]:
    expanded: List[str] = []
    for target in targets:
        if target == "all":
            for name in TARGETS:
                if name not in expanded:
                    expanded.append(name)
            continue
        if target not in TARGETS:
            raise GenerationError(f"unknown target: {target}")
        if target not in expanded:
            expanded.append(target)
    return expanded


def load_openapi(openapi_path: Path = OPENAPI_PATH) -> dict:
    ensure_openapi_exists(openapi_path)
    with openapi_path.open() as spec_file:
        return json.load(spec_file)


def generated_paths(root: Path = REPO_ROOT) -> List[Path]:
    return [
        root / "rust" / "src" / "models.rs",
        root / "python" / "everruns_sdk" / "models.py",
        root / "typescript" / "src" / "models.ts",
    ]


def file_contents(paths: Sequence[Path]) -> dict[Path, bytes | None]:
    return {path: path.read_bytes() if path.is_file() else None for path in paths}


def generate_targets(targets: Sequence[str], root: Path = REPO_ROOT) -> List[Path]:
    openapi_path = root / "openapi" / "openapi.json"
    ensure_openapi_exists(openapi_path)
    paths = generate_public_models(
        load_openapi(openapi_path),
        load_config(root / "codegen" / "sdk-models.json"),
        rust_output=root / "rust" / "src" / "models.rs",
        python_output=root / "python" / "everruns_sdk" / "models.py",
        typescript_output=root / "typescript" / "src" / "models.ts",
        targets=targets,
    )
    format_generated(paths, root)
    return paths


def format_generated(paths: Sequence[Path], root: Path = REPO_ROOT) -> None:
    for path in paths:
        if path == root / "rust" / "src" / "models.rs":
            command = ["rustfmt", "--edition", "2021", str(path)]
            cwd = root
        elif path == root / "python" / "everruns_sdk" / "models.py":
            command = python_formatter_command(root, path)
            cwd = root
        else:
            command = ["npx", "prettier", "--write", str(path)]
            cwd = root / "typescript"
        subprocess.run(command, cwd=str(cwd), check=True)


def python_formatter_command(
    root: Path, output: Path, *, which: Callable[[str], Optional[str]] = shutil.which
) -> List[str]:
    ruff = root / "python" / ".venv" / "bin" / "ruff"
    if ruff.is_file():
        return [str(ruff), "format", str(output)]

    uv = which("uv")
    command = [uv] if uv else [sys.executable, "-m", "uv"]
    return command + [
        "run",
        "--project",
        str(root / "python"),
        "ruff",
        "format",
        str(output),
    ]


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        action="append",
        choices=("all",) + TARGETS,
        default=None,
        help="SDK target to regenerate. May be repeated.",
    )
    parser.add_argument(
        "--sync-openapi",
        action="store_true",
        help="Replace openapi/openapi.json with the upstream Everruns spec before generating.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if generated public model modules differ from checked-in files.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        targets = expand_targets(args.target or ["all"])
        if args.sync_openapi:
            sync_openapi()
        before = file_contents(generated_paths()) if args.check else {}
        paths = generate_targets(targets)
        if args.check and any(before[path] != path.read_bytes() for path in paths):
            print(
                "generated public models are stale; run `just generate`",
                file=sys.stderr,
            )
            return 1
    except (
        CodegenError,
        GenerationError,
        OSError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"generation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
