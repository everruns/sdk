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
#[derive(Debug, serde::Deserialize)]
pub struct ApiErrorResponse {
    pub error: ApiErrorDetail,
}

#[derive(Debug, serde::Deserialize)]
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
            Error::Api {
                code: "unknown".to_string(),
                message: body.to_string(),
                status,
            }
        }
    }
}

/// Result type for Everruns SDK operations
pub type Result<T> = std::result::Result<T, Error>;
