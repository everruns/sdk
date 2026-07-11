#!/usr/bin/env python3
"""Tests for the SDK public-model generator."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import generate as sdk_generate
import sdk_codegen


def small_spec() -> dict:
    return {
        "openapi": "3.1.0",
        "paths": {},
        "components": {
            "schemas": {
                "Agent": {
                    "type": "object",
                    "required": ["id"],
                    "properties": {
                        "id": {"type": "string"},
                        "display_name": {"type": ["string", "null"]},
                    },
                },
                "WithUrls_Agent": {
                    "type": "object",
                    "x-sdk-response-wrapper": {
                        "kind": "resource",
                        "model": "#/components/schemas/Agent",
                    },
                },
            }
        },
    }


class GenerateTests(unittest.TestCase):
    def test_expand_targets_deduplicates_all(self) -> None:
        self.assertEqual(
            sdk_generate.expand_targets(["python", "all", "python"]),
            ["python", "rust", "typescript"],
        )

    def test_response_wrapper_metadata_is_validated(self) -> None:
        wrappers = sdk_codegen.response_wrappers(small_spec())
        self.assertEqual(
            wrappers["WithUrls_Agent"],
            {"kind": "resource", "model": "Agent"},
        )

    def test_response_wrapper_rejects_unknown_kind(self) -> None:
        spec = small_spec()
        spec["components"]["schemas"]["WithUrls_Agent"]["x-sdk-response-wrapper"][
            "kind"
        ] = "envelope"
        with self.assertRaises(sdk_codegen.CodegenError):
            sdk_codegen.response_wrappers(spec)

    def test_wrapped_model_must_be_public(self) -> None:
        with self.assertRaisesRegex(
            sdk_codegen.CodegenError, "unconfigured public models: Agent"
        ):
            sdk_codegen.build_models(small_spec(), {"models": []})

    def test_build_models_supports_aliases_and_synthetic_models(self) -> None:
        models = sdk_codegen.build_models(
            small_spec(),
            {
                "models": ["Agent"],
                "aliases": {"PublicAgent": "Agent"},
                "syntheticSchemas": {"Options": {"type": "object"}},
            },
        )
        self.assertEqual(
            [model.name for model in models], ["Agent", "PublicAgent", "Options"]
        )

    def test_typescript_generation_uses_public_casing(self) -> None:
        models = sdk_codegen.build_models(small_spec(), {"models": ["Agent"]})
        output = sdk_codegen.TypeScriptEmitter(
            models, small_spec()["components"]["schemas"], {}
        ).emit()
        self.assertIn("displayName?: string | null;", output)
        self.assertNotIn("WithUrls_Agent", output)

    def test_typescript_emits_wire_decode_map(self) -> None:
        models = sdk_codegen.build_models(small_spec(), {"models": ["Agent"]})
        output = sdk_codegen.TypeScriptEmitter(
            models, small_spec()["components"]["schemas"], {}
        ).emit()
        # Multi-word wire keys map to their camelCase property. (Raw emit quotes
        # the keys; prettier strips the quotes when the file is written out.)
        self.assertIn('"display_name": { name: "displayName" }', output)
        # A generic decoder is exported for the response path.
        self.assertIn(
            "export function decodeModel<T>(value: unknown, model: string): T",
            output,
        )
        # Single-word keys need no entry (they pass through untouched).
        self.assertNotIn('"id":', output)

    def test_generation_is_deterministic_and_targeted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            outputs = {
                "rust_output": root / "models.rs",
                "python_output": root / "models.py",
                "typescript_output": root / "models.ts",
            }
            config = {"models": ["Agent"]}
            first = sdk_codegen.generate_public_models(
                small_spec(), config, targets=["typescript"], **outputs
            )
            content = outputs["typescript_output"].read_text()
            second = sdk_codegen.generate_public_models(
                small_spec(), config, targets=["typescript"], **outputs
            )
            second_content = outputs["typescript_output"].read_text()
            rust_exists = outputs["rust_output"].exists()
            python_exists = outputs["python_output"].exists()

        self.assertEqual(first, second)
        self.assertEqual(content, second_content)
        self.assertFalse(rust_exists)
        self.assertFalse(python_exists)

    def test_python_formatter_prefers_project_venv(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            ruff = root / "python" / ".venv" / "bin" / "ruff"
            ruff.parent.mkdir(parents=True)
            ruff.touch()
            output = root / "python" / "everruns_sdk" / "models.py"

            command = sdk_generate.python_formatter_command(root, output)

        self.assertEqual(command, [str(ruff), "format", str(output)])

    def test_python_formatter_supports_standalone_uv(self) -> None:
        root = Path("/repo")
        output = root / "python" / "everruns_sdk" / "models.py"

        command = sdk_generate.python_formatter_command(
            root, output, which=lambda name: "/bin/uv" if name == "uv" else None
        )

        self.assertEqual(command[:2], ["/bin/uv", "run"])

    def test_python_formatter_falls_back_to_uv_module(self) -> None:
        root = Path("/repo")
        output = root / "python" / "everruns_sdk" / "models.py"

        command = sdk_generate.python_formatter_command(
            root, output, which=lambda _name: None
        )

        self.assertEqual(command[1:4], ["-m", "uv", "run"])

    def test_checked_in_contract_resolves_and_has_no_cost_tier(self) -> None:
        root = Path(__file__).resolve().parents[1]
        spec = json.loads((root / "openapi" / "openapi.json").read_text())
        config = sdk_codegen.load_config(root / "codegen" / "sdk-models.json")

        models = sdk_codegen.build_models(spec, config)
        wrappers = sdk_codegen.response_wrappers(spec)

        self.assertIn("Agent", {model.name for model in models})
        self.assertEqual(len(wrappers), 7)
        self.assertNotIn('"x-cost-tier"', json.dumps(spec))

        python_output = sdk_codegen.PythonEmitter(
            models, spec["components"]["schemas"], config
        ).emit()
        typescript_output = sdk_codegen.TypeScriptEmitter(
            models, spec["components"]["schemas"], config
        ).emit()
        rust_output = sdk_codegen.RustEmitter(
            models, spec["components"]["schemas"], config
        ).emit()
        self.assertIn("class BudgetPeriod(BaseModel):", python_output)
        self.assertIn("export interface BudgetPeriod", typescript_output)
        self.assertIn('BuiltinTool & { type: "builtin" }', typescript_output)
        self.assertIn("data: Record<string, unknown>", typescript_output)
        self.assertIn("ClientSide(ClientSideTool)", rust_output)


if __name__ == "__main__":
    unittest.main()
