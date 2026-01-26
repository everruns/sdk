//! Everruns SDK for Rust
//!
//! This crate provides a typed client for the Everruns API.
//!
//! # Quick Start
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
//!         "Assistant",
//!         "You are a helpful assistant."
//!     ).await?;
//!
//!     // Create a session
//!     let session = client.sessions().create(&agent.id).await?;
//!
//!     // Send a message
//!     client.messages().create(&session.id, "Hello!").await?;
//!
//!     Ok(())
//! }
//! ```

pub mod auth;
pub mod client;
pub mod error;
pub mod models;
pub mod sse;

pub use auth::ApiKey;
pub use client::Everruns;
pub use error::Error;
pub use models::*;
