//! Authentication utilities

use secrecy::{ExposeSecret, SecretString};

/// API key for authenticating with Everruns
#[derive(Clone)]
pub struct ApiKey(SecretString);

impl ApiKey {
    /// Create a new API key from a string
    pub fn new(key: impl Into<String>) -> Self {
        Self(SecretString::from(key.into()))
    }

    /// Create an API key from the EVERRUNS_API_KEY environment variable
    pub fn from_env() -> Result<Self, crate::Error> {
        std::env::var("EVERRUNS_API_KEY")
            .map(ApiKey::new)
            .map_err(|_| crate::Error::EnvVar("EVERRUNS_API_KEY".to_string()))
    }

    /// Get the API key value (for use in headers)
    pub(crate) fn expose(&self) -> &str {
        self.0.expose_secret()
    }
}

impl std::fmt::Debug for ApiKey {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let key = self.expose();
        if key.len() > 8 {
            write!(f, "ApiKey({}...)", &key[..8])
        } else {
            write!(f, "ApiKey(***)")
        }
    }
}
