//! Error types for Everruns SDK

use thiserror::Error;

/// Errors that can occur when using the Everruns SDK
#[derive(Error, Debug)]
pub enum Error {
    /// API returned an error response
    #[error("API error: {code} - {message}")]
    Api {
        code: String,
        message: String,
        status: u16,
    },

    /// Network or HTTP error
    #[error("Network error: {0}")]
    Network(#[from] reqwest::Error),

    /// Authentication error
    #[error("Authentication error: {0}")]
    Auth(String),

    /// Environment variable not found
    #[error("Environment variable not found: {0}")]
    EnvVar(String),

    /// JSON serialization/deserialization error
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),

    /// URL parsing error
    #[error("URL error: {0}")]
    Url(#[from] url::ParseError),

    /// SSE stream error
    #[error("SSE error: {0}")]
    Sse(String),
}

/// API error response from the server
#[derive(Debug, serde::Serialize, serde::Deserialize)]
#[non_exhaustive]
pub struct ApiErrorResponse {
    pub error: ApiErrorDetail,
}

/// Detail of an API error
#[derive(Debug, serde::Serialize, serde::Deserialize)]
#[non_exhaustive]
pub struct ApiErrorDetail {
    pub code: String,
    pub message: String,
}

impl Error {
    pub(crate) fn from_api_response(status: u16, body: &str) -> Self {
        if let Ok(err) = serde_json::from_str::<ApiErrorResponse>(body) {
            Error::Api {
                code: err.error.code,
                message: err.error.message,
                status,
            }
        } else {
            // Simplify HTML responses to avoid verbose error messages
            let message = if is_html_response(body) {
                format!("HTTP {status}")
            } else {
                body.to_string()
            };
            Error::Api {
                code: "unknown".to_string(),
                message,
                status,
            }
        }
    }
}

/// Check if the body looks like an HTML response
fn is_html_response(body: &str) -> bool {
    let trimmed = body.trim_start();
    trimmed.starts_with("<!DOCTYPE") || trimmed.starts_with("<html") || trimmed.starts_with("<HTML")
}

/// Result type for Everruns SDK operations
pub type Result<T> = std::result::Result<T, Error>;
