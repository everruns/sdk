# Authentication

## API Key And Organization Context

All SDKs use `EVERRUNS_API_KEY` as the default API key source. Multi-org API-key users can set organization context with `EVERRUNS_ORG_ID` or an explicit client option. Explicit client options take precedence over the environment.

### Rust

```rust
use everruns_sdk::Everruns;

// From environment: EVERRUNS_API_KEY, optional EVERRUNS_API_URL, optional EVERRUNS_ORG_ID
let client = Everruns::from_env()?;

// Explicit
let client = Everruns::builder()
    .api_key("evr_...")
    .org_id("org_...")
    .build()?;
```

### Python

```python
from everruns_sdk import Everruns

# From environment: EVERRUNS_API_KEY, optional EVERRUNS_API_URL, optional EVERRUNS_ORG_ID
client = Everruns()

# Explicit
client = Everruns(api_key="evr_...", org_id="org_...")
```

### TypeScript

```typescript
import { Everruns } from "@everruns/sdk";

// From environment: EVERRUNS_API_KEY, optional EVERRUNS_API_URL, optional EVERRUNS_ORG_ID
const client = Everruns.fromEnv();

// Explicit
const client = new Everruns({ apiKey: "evr_...", orgId: "org_..." });
```

## Auth Header Format

```
Authorization: <api_key>
X-Org-Id: <org_id>
```

No Bearer prefix for API keys. Keys start with `evr_` prefix. `X-Org-Id` is optional for single-org accounts and required by the API when an API key has access to multiple organizations.
