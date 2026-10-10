//! Everruns SDK for Rust
//!
//! This crate provides a typed client for the Everruns API.
//!
//! # Call your agent from code
//!
//! To call an agent from an application, use [`AgentClient`] with an agent key. The
//! management client [`Everruns`] below is for managing Everruns (agents,
//! harnesses, workspaces) with a personal access token.
//!
//! ```rust,no_run
//! use everruns_sdk::AgentClient;
//!
//! #[tokio::main]
//! async fn main() -> Result<(), everruns_sdk::Error> {
//!     // EVERRUNS_AGENT_URL and EVERRUNS_AGENT_KEY
//!     let agent = AgentClient::from_env()?;
//!     println!("{}", agent.run("Hello!", None).await?);
//!     Ok(())
//! }
//! ```
//!
//! # Quick Start (management client)
//!
//! ```rust,no_run
//! use everruns_sdk::Everruns;
//!
//! #[tokio::main]
//! async fn main() -> Result<(), everruns_sdk::Error> {
//!     // Uses EVERRUNS_API_KEY environment variable
//!     let client = Everruns::from_env()?;
//!
//!     // Create an agent
//!     let agent = client.agents().create(
//!         "assistant",
//!         "You are a helpful assistant."
//!     ).await?;
//!
//!     // Create a session
//!     let session = client.sessions().create().await?;
//!
//!     // Send a message
//!     client.messages().create(&session.id, "Hello!").await?;
//!
//!     Ok(())
//! }
//! ```

pub mod agent;
pub mod auth;
pub mod client;
pub mod error;
pub mod models;
pub mod sse;

pub use agent::{
    AgentCard, AgentCardAuth, AgentCardInput, AgentCardLinks, AgentClient, AgentClientBuilder,
    AgentEventList, AgentSession, AgentSessionList, RuntimeToken,
};
pub use auth::ApiKey;
pub use client::{CHANGE_REASON_HEADER, Everruns, MAX_CHANGE_REASON_CHARS};
pub use error::Error;
pub use models::*;
