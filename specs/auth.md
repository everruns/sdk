# Authentication

## Personal Access Token And Organization Context

All SDKs use `EVERRUNS_API_KEY` as the default personal access token source. Multi-org token users can set organization context with `EVERRUNS_ORG_ID` or an explicit client option. Explicit client options take precedence over the environment.

### Rust

```rust
use everruns_sdk::Everruns;

// From environment: EVERRUNS_API_KEY, optional EVERRUNS_API_URL, optional EVERRUNS_ORG_ID
let client = Everruns::from_env()?;

// Explicit
let client = Everruns::builder()
    .api_key("evr_pat_...")
    .org_id("org_...")
    .build()?;
```

### Python

```python
from everruns_sdk import Everruns

# From environment: EVERRUNS_API_KEY, optional EVERRUNS_API_URL, optional EVERRUNS_ORG_ID
client = Everruns()

# Explicit
client = Everruns(api_key="evr_pat_...", org_id="org_...")
```

### TypeScript

```typescript
import { Everruns } from "@everruns/sdk";

// From environment: EVERRUNS_API_KEY, optional EVERRUNS_API_URL, optional EVERRUNS_ORG_ID
const client = Everruns.fromEnv();

// Explicit
const client = new Everruns({ apiKey: "evr_pat_...", orgId: "org_..." });
```

## Auth Header Format

```
Authorization: <personal_access_token>
X-Org-Id: <org_id>
```

No Bearer prefix. Personal access tokens start with the `evr_pat_` prefix. `X-Org-Id` is optional for single-org accounts and required by the API when a token has access to multiple organizations.
