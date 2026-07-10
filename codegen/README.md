# SDK model generation

`sdk-models.json` is the SDK-owned overlay for public model generation. The
OpenAPI document remains the source of truth for wire fields, types, required
properties, enums, descriptions, and validation constraints.

The generator consumes `x-sdk-response-wrapper` from OpenAPI component schemas:

```json
{
  "x-sdk-response-wrapper": {
    "kind": "resource",
    "model": "#/components/schemas/Agent"
  }
}
```

`kind` is `resource` or `list`. `model` must reference a configured public
schema. Wrapper schemas are transport envelopes and are not emitted as public
SDK models.

The overlay contains only SDK policy that OpenAPI cannot express without
language coupling:

- the schemas included in the public SDK surface;
- stable public aliases and SDK-only option/helper models;
- historical field casing, ordering, and optionality needed for compatibility;
- language-specific type names and generated builder/union shapes.

Do not duplicate ordinary OpenAPI fields in the overlay. Fix incorrect wire
schemas upstream. Add an `x-sdk-*` extension upstream only for server-owned
semantic information shared by all SDK languages.

Run `just sync-openapi` to update the mirror and regenerate all public models.
Run `just generate-check` to verify checked-in outputs are current.
