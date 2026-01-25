# Authentication

## EVERRUNS_API_KEY

All SDKs use `EVERRUNS_API_KEY` environment variable as default.

### Rust

```rust
use everruns_sdk::Everruns;

// From environment
let client = Everruns::from_env("my-org")?;

// Explicit
let client = Everruns::new("evr_...", "my-org");
```

### Python

```python
from everruns_sdk import Everruns

# From environment
client = Everruns(org="my-org")

# Explicit
client = Everruns(api_key="evr_...", org="my-org")
```

### TypeScript

```typescript
import { Everruns } from "@everruns/sdk";

// From environment
const client = Everruns.fromEnv("my-org");

// Explicit
const client = new Everruns({ apiKey: "evr_...", org: "my-org" });
```

## Auth Header Format

```
Authorization: <api_key>
```

No Bearer prefix for API keys. Keys start with `evr_` prefix.
