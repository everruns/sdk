//! Shared utilities for Everruns SDK cookbook examples
//!
//! Provides helpers for creating dev clients and cleanup.

use everruns_sdk::{Error, Everruns};

/// Create a client configured for dev/local environment.
///
/// # Environment Variables
///
/// - `EVERRUNS_ORG` (required): Organization ID
/// - `EVERRUNS_API_KEY` (required): API key
/// - `EVERRUNS_API_URL` (optional): Custom API URL for dev/staging
///
/// # Panics
///
/// Panics if required environment variables are not set.
pub fn dev_client() -> Result<Everruns, Error> {
    let org = std::env::var("EVERRUNS_ORG").expect("EVERRUNS_ORG must be set");
    let api_key = std::env::var("EVERRUNS_API_KEY").expect("EVERRUNS_API_KEY must be set");

    if let Ok(base_url) = std::env::var("EVERRUNS_API_URL") {
        Everruns::with_base_url(api_key, org, &base_url)
    } else {
        Everruns::new(api_key, org)
    }
}

/// Cleanup helper - delete session and agent, ignoring errors.
pub async fn cleanup(client: &Everruns, session_id: &str, agent_id: &str) {
    if let Err(e) = client.sessions().delete(session_id).await {
        tracing::warn!("Failed to delete session {}: {}", session_id, e);
    }
    if let Err(e) = client.agents().delete(agent_id).await {
        tracing::warn!("Failed to delete agent {}: {}", agent_id, e);
    }
}

/// Cleanup helper - delete only session, ignoring errors.
pub async fn cleanup_session(client: &Everruns, session_id: &str) {
    if let Err(e) = client.sessions().delete(session_id).await {
        tracing::warn!("Failed to delete session {}: {}", session_id, e);
    }
}

/// Cleanup helper - delete only agent, ignoring errors.
pub async fn cleanup_agent(client: &Everruns, agent_id: &str) {
    if let Err(e) = client.agents().delete(agent_id).await {
        tracing::warn!("Failed to delete agent {}: {}", agent_id, e);
    }
}

/// Initialize tracing for cookbook examples.
pub fn init_tracing() {
    use tracing_subscriber::{EnvFilter, fmt, prelude::*};

    tracing_subscriber::registry()
        .with(fmt::layer())
        .with(EnvFilter::from_default_env().add_directive("info".parse().unwrap()))
        .init();
}
