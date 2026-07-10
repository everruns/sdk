#!/usr/bin/env python3
"""Generate the three public SDK model modules from OpenAPI."""

from __future__ import annotations

import json
import keyword
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


RESPONSE_WRAPPER_EXTENSION = "x-sdk-response-wrapper"
VALID_WRAPPER_KINDS = {"list", "resource"}
RUST_KEYWORDS = {
    "as",
    "async",
    "await",
    "break",
    "const",
    "continue",
    "crate",
    "dyn",
    "else",
    "enum",
    "extern",
    "false",
    "fn",
    "for",
    "if",
    "impl",
    "in",
    "let",
    "loop",
    "match",
    "mod",
    "move",
    "mut",
    "pub",
    "ref",
    "return",
    "self",
    "Self",
    "static",
    "struct",
    "super",
    "trait",
    "true",
    "type",
    "union",
    "unsafe",
    "use",
    "where",
    "while",
}


class CodegenError(RuntimeError):
    """Raised when the SDK model contract is invalid."""


@dataclass(frozen=True)
class Model:
    name: str
    schema: Mapping[str, Any]


def load_config(path: Path) -> dict[str, Any]:
    with path.open() as config_file:
        config = json.load(config_file)
    if not isinstance(config, dict):
        raise CodegenError("SDK model config must be a JSON object")
    return config


def component_schemas(spec: Mapping[str, Any]) -> Mapping[str, Any]:
    schemas = spec.get("components", {}).get("schemas", {})
    if not isinstance(schemas, dict):
        raise CodegenError("OpenAPI components.schemas must be an object")
    return schemas


def ref_name(ref: str) -> str:
    prefix = "#/components/schemas/"
    if not ref.startswith(prefix):
        raise CodegenError(f"unsupported schema reference: {ref}")
    return ref.removeprefix(prefix)


def response_wrappers(spec: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    schemas = component_schemas(spec)
    wrappers: dict[str, dict[str, str]] = {}
    for schema_name, schema in schemas.items():
        if not isinstance(schema, dict) or RESPONSE_WRAPPER_EXTENSION not in schema:
            continue
        extension = schema[RESPONSE_WRAPPER_EXTENSION]
        if not isinstance(extension, dict):
            raise CodegenError(
                f"{schema_name}.{RESPONSE_WRAPPER_EXTENSION} must be an object"
            )
        kind = extension.get("kind")
        model_ref = extension.get("model")
        if kind not in VALID_WRAPPER_KINDS:
            raise CodegenError(f"{schema_name} has invalid SDK wrapper kind: {kind!r}")
        if not isinstance(model_ref, str):
            raise CodegenError(
                f"{schema_name} SDK wrapper model must be a schema reference"
            )
        model_name = ref_name(model_ref)
        if model_name not in schemas:
            raise CodegenError(
                f"{schema_name} SDK wrapper references missing model {model_name}"
            )
        wrappers[str(schema_name)] = {"kind": str(kind), "model": model_name}
    return wrappers


def build_models(spec: Mapping[str, Any], config: Mapping[str, Any]) -> list[Model]:
    schemas = component_schemas(spec)
    wrappers = response_wrappers(spec)
    if not wrappers:
        raise CodegenError(
            f"OpenAPI does not define any {RESPONSE_WRAPPER_EXTENSION} metadata"
        )

    models: list[Model] = []
    seen: set[str] = set()
    for name in config.get("models", []):
        if name not in schemas:
            raise CodegenError(
                f"configured public schema is missing from OpenAPI: {name}"
            )
        schema = config.get("schemaOverrides", {}).get(name, schemas[name])
        models.append(Model(str(name), schema))
        seen.add(str(name))

    for public_name, schema_name in config.get("aliases", {}).items():
        if schema_name not in schemas:
            raise CodegenError(
                f"configured schema alias target is missing: {schema_name}"
            )
        if public_name in seen:
            raise CodegenError(f"duplicate public model: {public_name}")
        models.append(Model(str(public_name), schemas[schema_name]))
        seen.add(str(public_name))

    for name, schema in config.get("syntheticSchemas", {}).items():
        if name in seen:
            raise CodegenError(f"duplicate public model: {name}")
        if not isinstance(schema, dict):
            raise CodegenError(f"synthetic schema {name} must be an object")
        models.append(Model(str(name), schema))
        seen.add(str(name))

    wrapped_models = {wrapper["model"] for wrapper in wrappers.values()}
    missing_wrapped_models = wrapped_models.difference(config.get("models", []))
    if missing_wrapped_models:
        missing = ", ".join(sorted(missing_wrapped_models))
        raise CodegenError(
            f"SDK response wrappers reference unconfigured public models: {missing}"
        )

    return models


def is_nullable(schema: Mapping[str, Any]) -> bool:
    schema_type = schema.get("type")
    if isinstance(schema_type, list) and "null" in schema_type:
        return True
    return any(
        isinstance(item, dict) and item.get("type") == "null"
        for item in schema.get("oneOf", [])
    )


def without_null(schema: Mapping[str, Any]) -> Mapping[str, Any]:
    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        non_null = [item for item in schema_type if item != "null"]
        result = dict(schema)
        result["type"] = non_null[0] if len(non_null) == 1 else non_null
        return result
    one_of = schema.get("oneOf")
    if isinstance(one_of, list):
        non_null = [
            item
            for item in one_of
            if not (isinstance(item, dict) and item.get("type") == "null")
        ]
        if len(non_null) == 1 and isinstance(non_null[0], dict):
            result = dict(non_null[0])
            result.setdefault("description", schema.get("description"))
            return result
        result = dict(schema)
        result["oneOf"] = non_null
        return result
    return schema


def resolve_schema(
    schema: Mapping[str, Any], components: Mapping[str, Any]
) -> Mapping[str, Any]:
    ref = schema.get("$ref")
    if isinstance(ref, str):
        target = components.get(ref_name(ref))
        if not isinstance(target, dict):
            raise CodegenError(f"missing referenced schema: {ref}")
        return target
    return schema


def merge_object_schemas(
    parts: Iterable[Mapping[str, Any]], components: Mapping[str, Any]
) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    required: list[str] = []
    description = None
    for raw_part in parts:
        part = resolve_schema(raw_part, components)
        if "allOf" in part:
            part = merge_object_schemas(part["allOf"], components)
        properties.update(part.get("properties", {}))
        for field in part.get("required", []):
            if field not in required:
                required.append(field)
        description = description or part.get("description")
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "description": description,
    }


def union_variants(
    schema: Mapping[str, Any], components: Mapping[str, Any]
) -> list[tuple[str, dict[str, Any]]]:
    variants: list[tuple[str, dict[str, Any]]] = []
    for index, raw_variant in enumerate(schema.get("oneOf", []), start=1):
        if not isinstance(raw_variant, dict) or raw_variant.get("type") == "null":
            continue
        variant = merge_object_schemas(
            raw_variant.get("allOf", [raw_variant]), components
        )
        discriminator = variant.get("properties", {}).get("type", {})
        values = (
            discriminator.get("enum", []) if isinstance(discriminator, dict) else []
        )
        wire_name = str(values[0]) if len(values) == 1 else f"variant_{index}"
        variants.append((wire_name, variant))
    return variants


def flatten_union(
    schema: Mapping[str, Any], components: Mapping[str, Any]
) -> dict[str, Any]:
    variants = union_variants(schema, components)
    if not variants:
        return {"type": "object", "properties": {}}
    properties: dict[str, Any] = {}
    required_sets: list[set[str]] = []
    discriminator_values: list[str] = []
    for wire_name, variant in variants:
        discriminator_values.append(wire_name)
        properties.update(variant.get("properties", {}))
        required_sets.append(set(variant.get("required", [])))
    properties["type"] = {"type": "string", "enum": discriminator_values}
    required = sorted(set.intersection(*required_sets)) if required_sets else []
    if "type" not in required:
        required.insert(0, "type")
    return {
        "type": "object",
        "description": schema.get("description"),
        "properties": properties,
        "required": required,
    }


def snake_case(name: str) -> str:
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.replace("-", "_").lower()


def camel_case(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def pascal_case(name: str) -> str:
    special = {"waitingfortoolresults": "WaitingForToolResults"}
    if name in special:
        return special[name]
    return "".join(
        part[:1].upper() + part[1:] for part in re.split(r"[_-]", name) if part
    )


def first_line(description: Any) -> str | None:
    if not isinstance(description, str) or not description.strip():
        return None
    return " ".join(description.strip().splitlines()[0].split())


def object_schema(
    schema: Mapping[str, Any], components: Mapping[str, Any]
) -> Mapping[str, Any]:
    if "allOf" in schema:
        return merge_object_schemas(schema["allOf"], components)
    return schema


class Emitter:
    def __init__(
        self,
        models: Sequence[Model],
        components: Mapping[str, Any],
        config: Mapping[str, Any],
    ):
        self.models = models
        self.components = components
        self.config = config
        self.public_names = {model.name for model in models}

    def public_ref_name(self, ref: str) -> str:
        name = ref_name(ref)
        return str(self.config.get("referenceAliases", {}).get(name, name))

    def schema_for(self, model: Model, *, flatten: bool = False) -> Mapping[str, Any]:
        if flatten and "oneOf" in model.schema:
            return flatten_union(model.schema, self.components)
        return object_schema(model.schema, self.components)

    def compatibility_optional(self, model: str, field: str) -> bool:
        return f"{model}.{field}" in self.config.get("compatibilityOptionalFields", [])

    def properties_for(
        self, model: str, schema: Mapping[str, Any]
    ) -> list[tuple[str, Mapping[str, Any]]]:
        properties = schema.get("properties", {})
        order = self.config.get("fieldOrders", {}).get(model, [])
        names = list(order) + [name for name in properties if name not in order]
        return [(name, properties[name]) for name in names if name in properties]


class PythonEmitter(Emitter):
    flatten_models = {"BudgetPeriod", "ContentPart", "ToolDefinition"}

    def type_expr(self, schema: Mapping[str, Any]) -> str:
        nullable = is_nullable(schema)
        schema = without_null(schema)
        if "$ref" in schema:
            name = self.public_ref_name(str(schema["$ref"]))
            result = name if name in self.public_names else "Any"
        elif schema.get("enum"):
            result = (
                "Literal[" + ", ".join(repr(value) for value in schema["enum"]) + "]"
            )
        elif schema.get("oneOf"):
            choices = [
                self.type_expr(choice)
                for choice in schema["oneOf"]
                if choice.get("type") != "null"
            ]
            result = " | ".join(dict.fromkeys(choices)) or "Any"
        else:
            schema_type = schema.get("type")
            if schema_type == "string":
                result = "str"
            elif schema_type == "integer":
                result = "int"
            elif schema_type == "number":
                result = "float"
            elif schema_type == "boolean":
                result = "bool"
            elif schema_type == "array":
                result = f"list[{self.type_expr(schema.get('items', {}))}]"
            elif schema_type == "object" and isinstance(
                schema.get("additionalProperties"), dict
            ):
                result = f"dict[str, {self.type_expr(schema['additionalProperties'])}]"
            elif schema_type == "object":
                result = "dict[str, Any]"
            else:
                result = "Any"
        return f"Optional[{result}]" if nullable else result

    def emit_object(self, model: Model, schema: Mapping[str, Any]) -> list[str]:
        lines = [f"class {model.name}(BaseModel):"]
        description = first_line(schema.get("description"))
        if description:
            lines.append(f'    """{description}"""')
            lines.append("")
        properties = dict(self.properties_for(model.name, schema))
        required = set(schema.get("required", []))
        if not properties:
            lines.append("    pass")
        for wire_name, field_schema in properties.items():
            field_name = snake_case(wire_name)
            if keyword.iskeyword(field_name):
                field_name += "_"
            field_type = self.type_expr(field_schema)
            optional = wire_name not in required or self.compatibility_optional(
                model.name, wire_name
            )
            if optional and not field_type.startswith("Optional["):
                field_type = f"Optional[{field_type}]"
            if (
                optional
                and without_null(field_schema).get("type") == "array"
                and not is_nullable(field_schema)
            ):
                default = " = Field(default_factory=list)"
            elif optional or is_nullable(field_schema):
                default = " = None"
            else:
                default = ""
            if model.name == "ToolDefinition" and wire_name == "type":
                default = ' = "client_side"'
            if model.name == "Event" and wire_name == "context":
                default = " = Field(default_factory=lambda: EventContext())"
            default_value = (
                self.config.get("python", {})
                .get("defaultValues", {})
                .get(f"{model.name}.{wire_name}")
            )
            if default_value is not None:
                field_type = self.type_expr(field_schema)
                default = f" = {default_value!r}"
            if field_name != wire_name:
                if default == " = Field(default_factory=list)":
                    default = f' = Field(default_factory=list, alias="{wire_name}")'
                elif default:
                    default = f' = Field(default={default.removeprefix(" = ")}, alias="{wire_name}")'
                else:
                    default = f' = Field(alias="{wire_name}")'
            lines.append(f"    {field_name}: {field_type}{default}")

        lines.extend(["", "    model_config = ConfigDict(populate_by_name=True)"])

        if model.name == "ContentPart":
            lines.extend(
                [
                    "",
                    "    @staticmethod",
                    '    def make_text(text: str) -> "ContentPart":',
                    '        return ContentPart(type="text", text=text)',
                    "",
                    "    @staticmethod",
                    '    def make_tool_result(tool_call_id: str, result: Any) -> "ContentPart":',
                    '        return ContentPart(type="tool_result", tool_call_id=tool_call_id, result=result)',
                    "",
                    "    @staticmethod",
                    '    def make_tool_error(tool_call_id: str, error: str) -> "ContentPart":',
                    '        return ContentPart(type="tool_result", tool_call_id=tool_call_id, error=error)',
                    "",
                    "    def is_tool_call(self) -> bool:",
                    '        return self.type == "tool_call"',
                    "",
                    '    def as_tool_call(self) -> Optional["ToolCallInfo"]:',
                    "        if not self.is_tool_call() or not self.id or not self.name:",
                    "            return None",
                    "        return ToolCallInfo(id=self.id, name=self.name, arguments=self.arguments or {})",
                ]
            )
        elif model.name == "MessageInput":
            lines.extend(
                [
                    "",
                    "    @staticmethod",
                    '    def tool_results(results: list[ContentPart]) -> "MessageInput":',
                    '        return MessageInput(role="tool_result", content=results)',
                ]
            )
        elif model.name == "Event":
            lines.extend(
                [
                    "",
                    "    def tool_calls(self) -> list[ToolCallInfo]:",
                    "        return extract_tool_calls(self.data)",
                ]
            )
        return lines

    def emit(self) -> str:
        lines = [
            '"""Public data models generated from the Everruns OpenAPI document."""',
            "",
            "from __future__ import annotations",
            "",
            "import re",
            "import secrets",
            "from typing import Any, Literal, Optional",
            "",
            "from pydantic import BaseModel, ConfigDict, Field",
            "",
            "# Regenerate with `just generate`. Do not edit by hand.",
            "",
        ]
        class_names: list[str] = []
        deferred_aliases: list[str] = []
        for model in self.models:
            schema = self.schema_for(model, flatten=model.name in self.flatten_models)
            if schema.get("enum") and schema.get("type") == "string":
                values = ", ".join(repr(value) for value in schema["enum"])
                lines.extend([f"{model.name} = Literal[{values}]", ""])
            elif "oneOf" in schema:
                choices: list[str] = []
                for choice in schema["oneOf"]:
                    if "$ref" in choice:
                        choices.append(self.public_ref_name(choice["$ref"]))
                    elif "allOf" in choice:
                        refs = [part for part in choice["allOf"] if "$ref" in part]
                        choices.append(
                            self.public_ref_name(refs[0]["$ref"]) if refs else "Any"
                        )
                    else:
                        choices.append(self.type_expr(choice))
                deferred_aliases.extend(
                    [f"{model.name} = " + " | ".join(dict.fromkeys(choices)), ""]
                )
            else:
                lines.extend(self.emit_object(model, schema))
                lines.append("")
                class_names.append(model.name)

        lines.extend(
            [
                "class ListResponse(BaseModel):",
                "    data: list[Any]",
                "    total: int = 0",
                "    offset: int = 0",
                "    limit: int = 0",
                "",
            ]
        )
        class_names.append("ListResponse")
        lines.extend(deferred_aliases)
        lines.extend(
            [
                "def generate_agent_id() -> str:",
                '    return f"agent_{secrets.token_hex(16)}"',
                "",
                "",
                "def generate_harness_id() -> str:",
                '    return f"harness_{secrets.token_hex(16)}"',
                "",
                "",
                '_ADDRESSABLE_NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")',
                "_ADDRESSABLE_NAME_MAX_LENGTH = 64",
                "",
                "",
                "def _validate_addressable_name(name: str, *, label: str) -> str:",
                "    if len(name) > _ADDRESSABLE_NAME_MAX_LENGTH:",
                '        raise ValueError(f"{label} must be at most 64 characters, got {len(name)}")',
                "    if not _ADDRESSABLE_NAME_PATTERN.match(name):",
                '        raise ValueError(f"{label} must match pattern [a-z0-9]+(-[a-z0-9]+)*, got {name!r}")',
                "    return name",
                "",
                "",
                "def validate_harness_name(name: str) -> str:",
                '    return _validate_addressable_name(name, label="harness_name")',
                "",
                "",
                "def validate_agent_name(name: str) -> str:",
                '    return _validate_addressable_name(name, label="agent_name")',
                "",
                "",
                "def extract_tool_calls(data: dict[str, Any]) -> list[ToolCallInfo]:",
                '    requested = data.get("tool_calls")',
                "    if not isinstance(requested, list):",
                '        message = data.get("message")',
                '        requested = message.get("content", []) if isinstance(message, dict) else []',
                "    results: list[ToolCallInfo] = []",
                "    for call in requested:",
                "        if not isinstance(call, dict):",
                "            continue",
                '        if call.get("type") not in (None, "tool_call"):',
                "            continue",
                '        call_id, call_name = call.get("id"), call.get("name")',
                "        if call_id and call_name:",
                '            results.append(ToolCallInfo(id=call_id, name=call_name, arguments=call.get("arguments", {})))',
                "    return results",
                "",
            ]
        )
        lines.extend(f"{name}.model_rebuild()" for name in class_names)
        lines.append("")
        return "\n".join(lines)


class TypeScriptEmitter(Emitter):
    flatten_models = {"BudgetPeriod", "ContentPart"}

    def settings(self) -> Mapping[str, Any]:
        return self.config.get("typescript", {})

    def field_name(self, model: str, wire_name: str) -> str:
        override = self.settings().get("fieldRenames", {}).get(f"{model}.{wire_name}")
        if override:
            return str(override)
        if model in self.settings().get("snakeCaseModels", []):
            return wire_name
        return camel_case(wire_name)

    def type_expr(self, schema: Mapping[str, Any]) -> str:
        nullable = is_nullable(schema)
        schema = without_null(schema)
        if "$ref" in schema:
            name = self.public_ref_name(str(schema["$ref"]))
            result = name if name in self.public_names else "unknown"
        elif schema.get("enum"):
            result = " | ".join(json.dumps(value) for value in schema["enum"])
        elif schema.get("oneOf"):
            result = " | ".join(
                dict.fromkeys(
                    self.type_expr(choice)
                    for choice in schema["oneOf"]
                    if choice.get("type") != "null"
                )
            )
        else:
            schema_type = schema.get("type")
            if schema_type == "string":
                result = "string"
            elif schema_type in ("integer", "number"):
                result = "number"
            elif schema_type == "boolean":
                result = "boolean"
            elif schema_type == "array":
                item = self.type_expr(schema.get("items", {}))
                result = f"({item})[]" if " | " in item else f"{item}[]"
            elif schema_type == "object" and isinstance(
                schema.get("additionalProperties"), dict
            ):
                result = (
                    f"Record<string, {self.type_expr(schema['additionalProperties'])}>"
                )
            elif schema_type == "object":
                result = "Record<string, unknown>"
            else:
                result = "unknown"
        return f"{result} | null" if nullable else result

    def emit_object(self, model: Model, schema: Mapping[str, Any]) -> list[str]:
        lines: list[str] = []
        description = first_line(schema.get("description"))
        if description:
            lines.append(f"/** {description.replace('*/', '* /')} */")
        lines.append(f"export interface {model.name} {{")
        properties = dict(self.properties_for(model.name, schema))
        required = set(schema.get("required", []))
        omitted = set(self.settings().get("omitFields", {}).get(model.name, []))
        type_overrides = self.settings().get("typeOverrides", {})
        for wire_name, field_schema in properties.items():
            if wire_name in omitted:
                continue
            field_name = self.field_name(model.name, wire_name)
            optional = "" if wire_name in required else "?"
            field_type = type_overrides.get(
                f"{model.name}.{wire_name}", self.type_expr(field_schema)
            )
            lines.append(f"  {field_name}{optional}: {field_type};")
        lines.append("}")
        return lines

    def emit(self) -> str:
        lines = [
            "/** Public data models generated from the Everruns OpenAPI document. */",
            "",
            "// Regenerate with `just generate`. Do not edit by hand.",
            "",
        ]
        for model in self.models:
            schema = self.schema_for(model, flatten=model.name in self.flatten_models)
            if schema.get("enum") and schema.get("type") == "string":
                values = " | ".join(json.dumps(value) for value in schema["enum"])
                lines.extend([f"export type {model.name} = {values};", ""])
            elif "oneOf" in schema:
                choices: list[str] = []
                for choice in schema["oneOf"]:
                    if "$ref" in choice:
                        choices.append(self.public_ref_name(choice["$ref"]))
                    elif "allOf" in choice:
                        refs = [part for part in choice["allOf"] if "$ref" in part]
                        if refs:
                            choice_type = self.public_ref_name(refs[0]["$ref"])
                            inline = merge_object_schemas(
                                choice["allOf"], self.components
                            )
                            discriminator = inline.get("properties", {}).get("type", {})
                            values = discriminator.get("enum", [])
                            if len(values) == 1:
                                choice_type += f" & {{ type: {json.dumps(values[0])} }}"
                            choices.append(choice_type)
                        else:
                            choices.append(self.type_expr(choice))
                    else:
                        choices.append(self.type_expr(choice))
                lines.extend(
                    [
                        f"export type {model.name} = "
                        + " | ".join(dict.fromkeys(choices))
                        + ";",
                        "",
                    ]
                )
            else:
                lines.extend(self.emit_object(model, schema))
                lines.append("")

        lines.extend(
            [
                "export interface ListResponse<T> {",
                "  data: T[];",
                "  total: number;",
                "  offset: number;",
                "  limit: number;",
                "}",
                "",
                "export function generateAgentId(): string {",
                "  const bytes = new Uint8Array(16);",
                "  crypto.getRandomValues(bytes);",
                '  return `agent_${Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("")}`;',
                "}",
                "",
                "export function generateHarnessId(): string {",
                "  const bytes = new Uint8Array(16);",
                "  crypto.getRandomValues(bytes);",
                '  return `harness_${Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("")}`;',
                "}",
                "",
                "const ADDRESSABLE_NAME_PATTERN = /^[a-z0-9]+(-[a-z0-9]+)*$/;",
                "",
                "function validateAddressableName(name: string, label: string): void {",
                "  if (name.length > 64) throw new Error(`${label} must be at most 64 characters, got ${name.length}`);",
                '  if (!ADDRESSABLE_NAME_PATTERN.test(name)) throw new Error(`${label} must match pattern [a-z0-9]+(-[a-z0-9]+)*, got "${name}"`);',
                "}",
                "",
                "export function validateHarnessName(name: string): void {",
                '  validateAddressableName(name, "harness_name");',
                "}",
                "",
                "export function validateAgentName(name: string): void {",
                '  validateAddressableName(name, "agent_name");',
                "}",
                "",
                "export function toolResult(toolCallId: string, result: unknown): ContentPart {",
                '  return { type: "tool_result", tool_call_id: toolCallId, result };',
                "}",
                "",
                "export function toolError(toolCallId: string, error: string): ContentPart {",
                '  return { type: "tool_result", tool_call_id: toolCallId, error };',
                "}",
                "",
                "export function extractToolCalls(data: Record<string, unknown>): ToolCallInfo[] {",
                "  let requested = data.tool_calls;",
                "  if (!Array.isArray(requested)) requested = (data.message as { content?: unknown[] } | undefined)?.content ?? [];",
                "  if (!Array.isArray(requested)) return [];",
                "  return requested.flatMap((value) => {",
                "    const call = value as Record<string, unknown>;",
                '    if (call.type !== undefined && call.type !== "tool_call") return [];',
                '    if (typeof call.id !== "string" || typeof call.name !== "string") return [];',
                "    return [{ id: call.id, name: call.name, arguments: (call.arguments as Record<string, unknown>) ?? {} }];",
                "  });",
                "}",
                "",
            ]
        )
        return "\n".join(lines)


class RustEmitter(Emitter):
    builder_models = {
        "AgentCapabilityConfig",
        "BuiltinTool",
        "ClientSideTool",
        "ExternalActor",
        "InitialFile",
    }
    special_request_models = {
        "CreateFileRequest",
        "CreateMemoryFileRequest",
        "UpdateFileRequest",
        "UpdateMemoryFileRequest",
    }

    def settings(self) -> Mapping[str, Any]:
        return self.config.get("rust", {})

    def field_name(self, model: str, wire_name: str) -> str:
        override = self.settings().get("fieldRenames", {}).get(f"{model}.{wire_name}")
        if override:
            return str(override)
        name = snake_case(wire_name)
        if name == "type":
            return "kind"
        if name in RUST_KEYWORDS:
            return f"r#{name}"
        return name

    def type_expr(self, schema: Mapping[str, Any]) -> str:
        nullable = is_nullable(schema)
        schema = without_null(schema)
        if "$ref" in schema:
            name = self.public_ref_name(str(schema["$ref"]))
            result = name if name in self.public_names else "serde_json::Value"
        elif schema.get("enum") and len(schema["enum"]) == 1:
            result = "String"
        elif schema.get("oneOf"):
            result = "serde_json::Value"
        else:
            schema_type = schema.get("type")
            if schema_type == "string":
                result = "String"
            elif schema_type == "integer":
                format_name = schema.get("format")
                if format_name == "int32":
                    result = "i32"
                elif format_name == "uint32":
                    result = "u32"
                elif format_name in ("uint64", "usize") or (
                    schema.get("minimum") == 0 and format_name is None
                ):
                    result = "u64"
                else:
                    result = "i64"
            elif schema_type == "number":
                result = "f32" if schema.get("format") == "float" else "f64"
            elif schema_type == "boolean":
                result = "bool"
            elif schema_type == "array":
                result = f"Vec<{self.type_expr(schema.get('items', {}))}>"
            elif schema_type == "object" and isinstance(
                schema.get("additionalProperties"), dict
            ):
                result = f"std::collections::HashMap<String, {self.type_expr(schema['additionalProperties'])}>"
            else:
                result = "serde_json::Value"
        return f"Option<{result}>" if nullable else result

    def rust_field_type(
        self, model: str, wire_name: str, schema: Mapping[str, Any], required: bool
    ) -> str:
        override = self.settings().get("typeOverrides", {}).get(f"{model}.{wire_name}")
        field_type = str(override) if override else self.type_expr(schema)
        if f"{model}.{wire_name}" in self.settings().get("doubleOptionFields", []):
            return f"Option<{field_type}>"
        if f"{model}.{wire_name}" in self.settings().get("defaultFields", []):
            return field_type
        if required or field_type.startswith("Option<"):
            return field_type
        if without_null(schema).get("type") == "array":
            return field_type
        return f"Option<{field_type}>"

    def emit_enum(self, model: Model, schema: Mapping[str, Any]) -> list[str]:
        lines = [
            "#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]",
            f"pub enum {model.name} {{",
        ]
        for value in schema["enum"]:
            lines.extend(
                [f'    #[serde(rename = "{value}")]', f"    {pascal_case(str(value))},"]
            )
        lines.append("}")
        return lines

    def emit_union(self, model: Model, schema: Mapping[str, Any]) -> list[str]:
        variants = union_variants(schema, self.components)
        raw_variants = [
            variant
            for variant in schema.get("oneOf", [])
            if isinstance(variant, dict) and variant.get("type") != "null"
        ]
        lines = ["#[derive(Debug, Clone, Serialize, Deserialize)]"]
        if all("type" in variant.get("properties", {}) for _, variant in variants):
            lines.append('#[serde(tag = "type")]')
        else:
            lines.append("#[serde(untagged)]")
        lines.append(f"pub enum {model.name} {{")
        for index, (wire_name, variant) in enumerate(variants):
            lines.append(f'    #[serde(rename = "{wire_name}")]')
            if model.name in self.settings().get("newtypeUnions", []):
                raw_variant = raw_variants[index]
                parts = raw_variant.get("allOf", [raw_variant])
                refs = [
                    part["$ref"]
                    for part in parts
                    if isinstance(part, dict) and "$ref" in part
                ]
                if not refs:
                    raise CodegenError(
                        f"{model.name}.{wire_name} must reference a component schema"
                    )
                lines.append(
                    f"    {pascal_case(wire_name)}({self.public_ref_name(refs[0])}),"
                )
                continue
            omitted = set(
                self.settings()
                .get("unionOmitFields", {})
                .get(f"{model.name}.{wire_name}", [])
            )
            properties = [
                (name, value)
                for name, value in variant.get("properties", {}).items()
                if name != "type"
            ]
            properties = [
                (name, value) for name, value in properties if name not in omitted
            ]
            required = set(variant.get("required", []))
            if not properties:
                lines.append(f"    {pascal_case(wire_name)},")
                continue
            lines.append(f"    {pascal_case(wire_name)} {{")
            for wire_field, field_schema in properties:
                field_name = self.field_name(model.name, wire_field)
                field_type = self.rust_field_type(
                    model.name, wire_field, field_schema, wire_field in required
                )
                if wire_field not in required:
                    lines.append(
                        '        #[serde(default, skip_serializing_if = "Option::is_none")]'
                    )
                lines.append(f"        {field_name}: {field_type},")
            lines.append("    },")
        lines.append("}")
        return lines

    def emit_object(self, model: Model, schema: Mapping[str, Any]) -> list[str]:
        properties = dict(self.properties_for(model.name, schema))
        required = {
            field
            for field in schema.get("required", [])
            if not self.compatibility_optional(model.name, field)
        }
        derives = "Debug, Clone, Serialize, Deserialize"
        if not required:
            derives += ", Default"
        lines = [
            f"#[derive({derives})]",
            "#[non_exhaustive]",
            f"pub struct {model.name} {{",
        ]
        for wire_name, field_schema in properties.items():
            field_name = self.field_name(model.name, wire_name)
            field_type = self.rust_field_type(
                model.name, wire_name, field_schema, wire_name in required
            )
            if field_name != wire_name:
                lines.append(f'    #[serde(rename = "{wire_name}")]')
            if f"{model.name}.{wire_name}" in self.settings().get("defaultFields", []):
                lines.append("    #[serde(default)]")
            elif wire_name not in required:
                if field_type.startswith("Vec<"):
                    lines.append(
                        '    #[serde(default, skip_serializing_if = "Vec::is_empty")]'
                    )
                else:
                    lines.append(
                        '    #[serde(default, skip_serializing_if = "Option::is_none")]'
                    )
            elif model.name == "Event" and wire_name == "context":
                lines.append("    #[serde(default)]")
            lines.append(f"    pub {field_name}: {field_type},")
        lines.append("}")
        if model.name.endswith("Request") or model.name in self.builder_models:
            lines.extend(self.emit_builders(model, schema))
        return lines

    def constructor_param(self, name: str, field_type: str) -> str:
        if field_type == "String":
            return f"{name}: impl Into<String>"
        return f"{name}: {field_type}"

    def emit_builders(self, model: Model, schema: Mapping[str, Any]) -> list[str]:
        properties = dict(self.properties_for(model.name, schema))
        required_order = [
            name for name in schema.get("required", []) if name in properties
        ]
        required = set(required_order)
        lines = ["", f"impl {model.name} {{"]
        if model.name not in self.special_request_models:
            params: list[str] = []
            assignments: list[str] = []
            for wire_name in required_order:
                field_name = self.field_name(model.name, wire_name)
                field_type = self.rust_field_type(
                    model.name, wire_name, properties[wire_name], True
                )
                params.append(self.constructor_param(field_name, field_type))
            for wire_name, field_schema in properties.items():
                field_name = self.field_name(model.name, wire_name)
                field_type = self.rust_field_type(
                    model.name, wire_name, field_schema, wire_name in required
                )
                if wire_name in required:
                    value = (
                        f"{field_name}.into()" if field_type == "String" else field_name
                    )
                elif field_type.startswith("Vec<"):
                    value = "Vec::new()"
                else:
                    value = "None"
                if value == field_name:
                    assignments.append(f"            {field_name},")
                else:
                    assignments.append(f"            {field_name}: {value},")
            signature = ", ".join(params)
            lines.extend(
                [
                    f"    pub fn new({signature}) -> Self {{",
                    "        Self {",
                    *assignments,
                    "        }",
                    "    }",
                ]
            )

        suppressed = (
            {"content"}
            if model.name in {"UpdateFileRequest", "UpdateMemoryFileRequest"}
            else set()
        )
        for wire_name, field_schema in properties.items():
            if wire_name in required or wire_name in suppressed:
                continue
            field_name = self.field_name(model.name, wire_name)
            field_type = self.rust_field_type(
                model.name, wire_name, field_schema, False
            )
            lines.append("")
            if field_type.startswith("Option<Option<"):
                inner = field_type.removeprefix("Option<Option<").removesuffix(">>")
                param = f"{field_name}: Option<{inner}>"
                assignment = f"Some({field_name})"
            elif field_type.startswith("Option<String>"):
                param = f"{field_name}: impl Into<String>"
                assignment = f"Some({field_name}.into())"
            elif field_type.startswith("Option<"):
                inner = field_type.removeprefix("Option<").removesuffix(">")
                param = f"{field_name}: {inner}"
                assignment = f"Some({field_name})"
            else:
                param = f"{field_name}: {field_type}"
                assignment = field_name
            lines.extend(
                [
                    f"    pub fn {field_name}(mut self, {param}) -> Self {{",
                    f"        self.{field_name} = {assignment};",
                    "        self",
                    "    }",
                ]
            )

        if model.name in {"CreateFileRequest", "CreateMemoryFileRequest"}:
            lines.extend(
                [
                    "",
                    "    pub fn file(content: impl Into<String>) -> Self {",
                    "        Self { content: Some(content.into()), encoding: None, is_directory: None",
                    *(
                        [", is_readonly: None"]
                        if model.name == "CreateFileRequest"
                        else []
                    ),
                    "        }",
                    "    }",
                    "",
                    "    pub fn directory() -> Self {",
                    "        Self { content: None, encoding: None, is_directory: Some(true)",
                    *(
                        [", is_readonly: None"]
                        if model.name == "CreateFileRequest"
                        else []
                    ),
                    "        }",
                    "    }",
                ]
            )
        elif model.name in {"UpdateFileRequest", "UpdateMemoryFileRequest"}:
            fields = [
                self.field_name(model.name, name)
                for name in properties
                if name != "content"
            ]
            lines.extend(
                [
                    "",
                    "    pub fn content(content: impl Into<String>) -> Self {",
                    "        Self {",
                    "            content: Some(content.into()),",
                    *(f"            {field}: None," for field in fields),
                    "        }",
                    "    }",
                ]
            )
        lines.append("}")
        return lines

    def emit(self) -> str:
        lines = [
            "//! Public data models generated from the Everruns OpenAPI document.",
            "//!",
            "//! Regenerate with `just generate`. Do not edit by hand.",
            "",
            "use serde::{Deserialize, Serialize};",
            "",
        ]
        for model in self.models:
            if model.name == "ToolCallInfo":
                continue
            schema = self.schema_for(model)
            description = first_line(schema.get("description"))
            if description:
                lines.append(f"/// {description}")
            if schema.get("enum") and schema.get("type") == "string":
                lines.extend(self.emit_enum(model, schema))
            elif "oneOf" in schema:
                lines.extend(self.emit_union(model, schema))
            else:
                lines.extend(self.emit_object(model, schema))
            lines.append("")

        lines.extend(
            [
                "#[derive(Debug, Clone)]",
                "pub struct ToolCallInfo<'a> {",
                "    pub id: &'a str,",
                "    pub name: &'a str,",
                "    pub arguments: &'a serde_json::Value,",
                "}",
                "",
                "#[derive(Debug, Clone, Serialize, Deserialize)]",
                "#[non_exhaustive]",
                "pub struct ListResponse<T> {",
                "    pub data: Vec<T>,",
                "    #[serde(default)]",
                "    pub total: u64,",
                "    #[serde(default)]",
                "    pub offset: u64,",
                "    #[serde(default)]",
                "    pub limit: u64,",
                "}",
                "",
                "pub type DeleteResponse = DeleteFileResponse;",
                "",
                "impl ContentPart {",
                "    pub fn text(text: impl Into<String>) -> Self { Self::Text { text: text.into() } }",
                "",
                "    pub fn tool_result(tool_call_id: impl Into<String>, result: serde_json::Value) -> Self {",
                "        Self::ToolResult { tool_call_id: tool_call_id.into(), result: Some(result), error: None }",
                "    }",
                "",
                "    pub fn tool_error(tool_call_id: impl Into<String>, error: impl Into<String>) -> Self {",
                "        Self::ToolResult { tool_call_id: tool_call_id.into(), result: None, error: Some(error.into()) }",
                "    }",
                "",
                "    pub fn is_tool_call(&self) -> bool { matches!(self, Self::ToolCall { .. }) }",
                "",
                "    pub fn as_tool_call(&self) -> Option<ToolCallInfo<'_>> {",
                "        match self {",
                "            Self::ToolCall { id, name, arguments } => Some(ToolCallInfo { id, name, arguments }),",
                "            _ => None,",
                "        }",
                "    }",
                "}",
                "",
                "impl ToolDefinition {",
                "    pub fn client_side(name: impl Into<String>, description: impl Into<String>, parameters: serde_json::Value) -> Self {",
                "        Self::ClientSide(ClientSideTool::new(name, description, parameters))",
                "    }",
                "",
                "    pub fn builtin(name: impl Into<String>, description: impl Into<String>, parameters: serde_json::Value) -> Self {",
                "        Self::Builtin(BuiltinTool::new(name, description, parameters))",
                "    }",
                "}",
                "",
                "impl MessageInput {",
                "    pub fn new(role: MessageRole, content: Vec<ContentPart>) -> Self { Self { role, content } }",
                "",
                "    pub fn user_text(text: impl Into<String>) -> Self {",
                "        Self::new(MessageRole::User, vec![ContentPart::text(text)])",
                "    }",
                "",
                "    pub fn tool_results(results: Vec<ContentPart>) -> Self { Self::new(MessageRole::ToolResult, results) }",
                "}",
                "",
                "impl CreateMessageRequest {",
                "    pub fn user_text(text: impl Into<String>) -> Self { Self::new(MessageInput::user_text(text)) }",
                "}",
                "",
                "impl Event {",
                "    pub fn tool_calls(&self) -> Vec<ToolCallInfo<'_>> { extract_tool_calls(&self.data) }",
                "}",
                "",
                "pub fn extract_tool_calls(data: &serde_json::Value) -> Vec<ToolCallInfo<'_>> {",
                '    let requested = data.get("tool_calls").and_then(|value| value.as_array()).or_else(|| data.get("message")?.get("content")?.as_array());',
                "    requested.into_iter().flatten().filter_map(|part| {",
                '        if part.get("type").and_then(|value| value.as_str()).is_some_and(|kind| kind != "tool_call") { return None; }',
                "        Some(ToolCallInfo {",
                '            id: part.get("id")?.as_str()?,',
                '            name: part.get("name")?.as_str()?,',
                '            arguments: part.get("arguments").unwrap_or(&serde_json::Value::Null),',
                "        })",
                "    }).collect()",
                "}",
                "",
                'pub fn generate_agent_id() -> String { generate_id("agent") }',
                'pub fn generate_harness_id() -> String { generate_id("harness") }',
                "",
                "fn generate_id(prefix: &str) -> String {",
                "    let mut bytes = [0u8; 16];",
                '    getrandom::fill(&mut bytes).expect("failed to generate random bytes");',
                '    let hex: String = bytes.iter().map(|byte| format!("{byte:02x}")).collect();',
                '    format!("{prefix}_{hex}")',
                "}",
                "",
                'pub fn validate_harness_name(name: &str) -> crate::error::Result<()> { validate_addressable_name(name, "harness_name") }',
                'pub fn validate_agent_name(name: &str) -> crate::error::Result<()> { validate_addressable_name(name, "agent_name") }',
                "",
                "fn validate_addressable_name(name: &str, label: &str) -> crate::error::Result<()> {",
                '    if name.len() > 64 { return Err(crate::error::Error::Validation(format!("{label} must be at most 64 characters, got {}", name.len()))); }',
                "    let valid = !name.is_empty() && name.split('-').all(|part| !part.is_empty() && part.chars().all(|ch| ch.is_ascii_lowercase() || ch.is_ascii_digit()));",
                '    if !valid { return Err(crate::error::Error::Validation(format!("{label} must match pattern [a-z0-9]+(-[a-z0-9]+)*, got {name:?}"))); }',
                "    Ok(())",
                "}",
                "",
            ]
        )
        return "\n".join(lines)


def generate_public_models(
    spec: Mapping[str, Any],
    config: Mapping[str, Any],
    *,
    rust_output: Path,
    python_output: Path,
    typescript_output: Path,
    targets: Iterable[str] = ("rust", "python", "typescript"),
) -> list[Path]:
    models = build_models(spec, config)
    components = component_schemas(spec)
    emitters = {
        "rust": (rust_output, RustEmitter(models, components, config)),
        "python": (python_output, PythonEmitter(models, components, config)),
        "typescript": (
            typescript_output,
            TypeScriptEmitter(models, components, config),
        ),
    }
    outputs = {emitters[target][0]: emitters[target][1].emit() for target in targets}
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    return list(outputs)
