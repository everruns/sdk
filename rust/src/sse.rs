//! Server-Sent Events (SSE) streaming with automatic reconnection.
//!
//! Implements robust SSE streaming with:
//! - Automatic reconnection on disconnect
//! - Server retry hints
//! - Graceful handling of `disconnecting` events
//! - Exponential backoff for unexpected disconnections
//! - Resume from last event ID via `since_id`

use crate::client::Everruns;
use crate::error::{Error, Result};
use crate::models::Event;
use futures::stream::Stream;
use serde::Deserialize;
use std::future::Future;
use std::pin::Pin;
use std::task::{Context, Poll};
use std::time::Duration;
use tokio::time::{Sleep, sleep};

/// Maximum retry delay for exponential backoff
const MAX_RETRY_MS: u64 = 30_000;
/// Initial retry delay for exponential backoff
const INITIAL_BACKOFF_MS: u64 = 1000;
/// Read timeout for detecting stalled connections (2 minutes)
const READ_TIMEOUT_SECS: u64 = 120;

/// Options for SSE streaming
#[derive(Debug, Clone, Default)]
#[non_exhaustive]
pub struct StreamOptions {
    /// Event types to exclude from the stream
    pub exclude: Vec<String>,
    /// Resume from a specific event ID
    pub since_id: Option<String>,
    /// Maximum number of reconnection attempts (None = unlimited)
    pub max_retries: Option<u32>,
}

impl StreamOptions {
    /// Create new empty stream options
    pub fn new() -> Self {
        Self::default()
    }

    /// Create options that exclude delta events (for reduced bandwidth)
    pub fn exclude_deltas() -> Self {
        Self {
            exclude: vec![
                "output.message.delta".to_string(),
                "reason.thinking.delta".to_string(),
            ],
            since_id: None,
            max_retries: None,
        }
    }

    /// Set the event types to exclude
    pub fn with_exclude(mut self, exclude: Vec<String>) -> Self {
        self.exclude = exclude;
        self
    }

    /// Set the since_id for resuming a stream
    pub fn with_since_id(mut self, since_id: impl Into<String>) -> Self {
        self.since_id = Some(since_id.into());
        self
    }

    /// Set maximum retry attempts
    pub fn with_max_retries(mut self, max_retries: u32) -> Self {
        self.max_retries = Some(max_retries);
        self
    }
}

/// Data from a disconnecting event
#[derive(Debug, Clone, Deserialize)]
pub struct DisconnectingData {
    /// Reason for disconnection (e.g., "connection_cycle")
    pub reason: String,
    /// Suggested retry delay in milliseconds
    pub retry_ms: u64,
}

/// A stream of SSE events from a session with automatic reconnection.
///
/// This stream handles:
/// - Graceful `disconnecting` events from the server
/// - Unexpected connection drops with exponential backoff
/// - Server retry hints
/// - Automatic resume using `since_id`
///
/// # Example
///
/// ```no_run
/// use futures::StreamExt;
///
/// # async fn example() -> Result<(), Box<dyn std::error::Error>> {
/// let client = everruns_sdk::Everruns::new("your_api_key")?;
/// let mut stream = client.events().stream("session_id");
///
/// while let Some(result) = stream.next().await {
///     match result {
///         Ok(event) => println!("Event: {:?}", event.event_type),
///         Err(e) => eprintln!("Error: {}", e),
///     }
/// }
/// # Ok(())
/// # }
/// ```
pub struct EventStream {
    client: Everruns,
    session_id: String,
    options: StreamOptions,
    inner: Option<Pin<Box<dyn Stream<Item = Result<Event>> + Send>>>,
    last_event_id: Option<String>,
    /// Server-provided retry hint in milliseconds
    server_retry_ms: Option<u64>,
    /// Current backoff delay for unexpected disconnections
    current_backoff_ms: u64,
    /// Number of consecutive reconnection attempts
    retry_count: u32,
    /// Whether the stream should continue reconnecting
    should_reconnect: bool,
    /// Whether we received a graceful disconnect
    graceful_disconnect: bool,
    /// Pending delay before reconnection (non-blocking)
    delay_future: Option<Pin<Box<Sleep>>>,
}

impl EventStream {
    pub(crate) fn new(client: Everruns, session_id: String, options: StreamOptions) -> Self {
        Self {
            client,
            session_id,
            options,
            inner: None,
            last_event_id: None,
            server_retry_ms: None,
            current_backoff_ms: INITIAL_BACKOFF_MS,
            retry_count: 0,
            should_reconnect: true,
            graceful_disconnect: false,
            delay_future: None,
        }
    }

    /// Get the last received event ID (for resuming)
    pub fn last_event_id(&self) -> Option<&str> {
        self.last_event_id.as_deref()
    }

    /// Stop the stream and prevent further reconnection attempts
    pub fn stop(&mut self) {
        self.should_reconnect = false;
        self.inner = None;
        self.delay_future = None;
    }

    /// Get the current retry count
    pub fn retry_count(&self) -> u32 {
        self.retry_count
    }

    fn connect(&mut self) -> Pin<Box<dyn Stream<Item = Result<Event>> + Send>> {
        let client = self.client.clone();
        let session_id = self.session_id.clone();
        let since_id = self
            .last_event_id
            .clone()
            .or_else(|| self.options.since_id.clone());
        let exclude: Vec<String> = self.options.exclude.clone();

        Box::pin(async_stream::try_stream! {
            use reqwest_eventsource::{Event as SseEvent, EventSource};
            use futures::StreamExt;

            let exclude_refs: Vec<&str> = exclude.iter().map(|s| s.as_str()).collect();
            let url = client.sse_url(&session_id, since_id.as_deref(), &exclude_refs);

            tracing::debug!("Connecting to SSE: {}", url);

            let http_client = reqwest::Client::builder()
                .timeout(Duration::from_secs(0)) // No overall timeout for long-running streams
                .read_timeout(Duration::from_secs(READ_TIMEOUT_SECS)) // Detect stalled connections
                .build()
                .map_err(|e| Error::Sse(format!("Failed to create HTTP client: {}", e)))?;

            let request = http_client
                .get(url)
                .header("Authorization", client.auth_header())
                .header("Accept", "text/event-stream")
                .header("Cache-Control", "no-cache");

            let mut es = EventSource::new(request).map_err(|e| Error::Sse(e.to_string()))?;

            while let Some(event) = es.next().await {
                match event {
                    Ok(SseEvent::Open) => {
                        tracing::debug!("SSE connection opened");
                    }
                    Ok(SseEvent::Message(msg)) => {
                        // Handle special lifecycle events
                        if msg.event == "connected" {
                            tracing::debug!("SSE connected event received");
                            continue;
                        }

                        if msg.event == "disconnecting" {
                            // Parse disconnecting data for retry hint
                            if let Ok(data) = serde_json::from_str::<DisconnectingData>(&msg.data) {
                                tracing::debug!(
                                    "SSE disconnecting: reason={}, retry_ms={}",
                                    data.reason,
                                    data.retry_ms
                                );
                                // Signal graceful disconnect - the stream will handle reconnection
                                Err(Error::Sse(format!("__graceful_disconnect__:{}", data.retry_ms)))?;
                            } else {
                                tracing::debug!("SSE disconnecting event received (no data)");
                                Err(Error::Sse("__graceful_disconnect__:100".to_string()))?;
                            }
                        }

                        // Parse and yield regular events
                        if let Ok(event) = serde_json::from_str::<Event>(&msg.data) {
                            yield event;
                        } else {
                            tracing::debug!("Skipping non-event message: {}", msg.event);
                        }
                    }
                    Err(reqwest_eventsource::Error::StreamEnded) => {
                        tracing::debug!("SSE stream ended");
                        break;
                    }
                    Err(e) => {
                        tracing::warn!("SSE error: {}", e);
                        Err(Error::Sse(e.to_string()))?;
                    }
                }
            }
        })
    }

    fn get_retry_delay(&self) -> Duration {
        if self.graceful_disconnect {
            // Use server hint for graceful disconnect, or short default
            Duration::from_millis(self.server_retry_ms.unwrap_or(100))
        } else {
            // Use exponential backoff for unexpected disconnects
            Duration::from_millis(self.current_backoff_ms)
        }
    }

    fn update_backoff(&mut self) {
        if !self.graceful_disconnect {
            // Exponential backoff for unexpected disconnections
            self.current_backoff_ms = (self.current_backoff_ms * 2).min(MAX_RETRY_MS);
        }
    }

    fn reset_backoff(&mut self) {
        self.current_backoff_ms = INITIAL_BACKOFF_MS;
        self.retry_count = 0;
    }

    fn should_retry(&self) -> bool {
        if !self.should_reconnect {
            return false;
        }
        match self.options.max_retries {
            Some(max) => self.retry_count < max,
            None => true,
        }
    }

    fn schedule_reconnect(&mut self, delay: Duration) {
        self.delay_future = Some(Box::pin(sleep(delay)));
    }
}

impl Stream for EventStream {
    type Item = Result<Event>;

    fn poll_next(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Option<Self::Item>> {
        loop {
            // Check if we're waiting for a delay before reconnecting
            if let Some(ref mut delay) = self.delay_future {
                match Pin::new(delay).poll(cx) {
                    Poll::Ready(()) => {
                        // Delay completed, clear it and reconnect
                        self.delay_future = None;
                        self.graceful_disconnect = false;
                    }
                    Poll::Pending => {
                        // Still waiting for delay
                        return Poll::Pending;
                    }
                }
            }

            if self.inner.is_none() {
                if !self.should_reconnect {
                    return Poll::Ready(None);
                }
                self.inner = Some(self.connect());
            }

            let inner = self.inner.as_mut().unwrap();
            match Pin::new(inner).poll_next(cx) {
                Poll::Ready(Some(Ok(event))) => {
                    // Successfully received an event - reset backoff
                    self.reset_backoff();
                    self.last_event_id = Some(event.id.clone());
                    return Poll::Ready(Some(Ok(event)));
                }
                Poll::Ready(Some(Err(e))) => {
                    // Check if this is a graceful disconnect
                    let error_msg = e.to_string();
                    if error_msg.contains("__graceful_disconnect__") {
                        // Extract retry hint from error message
                        if let Some(ms_str) = error_msg.split("__graceful_disconnect__:").nth(1)
                            && let Ok(ms) = ms_str.parse::<u64>()
                        {
                            self.server_retry_ms = Some(ms);
                        }
                        self.graceful_disconnect = true;
                        self.inner = None;

                        if self.should_retry() {
                            self.retry_count += 1;
                            let delay = self.get_retry_delay();
                            tracing::debug!("Graceful reconnect in {:?}", delay);
                            self.schedule_reconnect(delay);
                            continue;
                        } else {
                            return Poll::Ready(None);
                        }
                    }

                    // Unexpected error - use exponential backoff
                    self.graceful_disconnect = false;
                    self.inner = None;

                    if self.should_retry() {
                        self.retry_count += 1;
                        let delay = self.get_retry_delay();
                        self.update_backoff();
                        tracing::debug!(
                            "Reconnecting after error in {:?} (attempt {})",
                            delay,
                            self.retry_count
                        );
                        self.schedule_reconnect(delay);
                        continue;
                    } else {
                        return Poll::Ready(Some(Err(e)));
                    }
                }
                Poll::Ready(None) => {
                    // Stream ended - always retry to handle read timeout case
                    self.inner = None;

                    if self.should_retry() {
                        self.retry_count += 1;
                        let delay = self.get_retry_delay();
                        self.update_backoff();
                        tracing::debug!(
                            "Stream ended, reconnecting in {:?} (attempt {})",
                            delay,
                            self.retry_count
                        );
                        self.schedule_reconnect(delay);
                        continue;
                    }

                    return Poll::Ready(None);
                }
                Poll::Pending => return Poll::Pending,
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_stream_options_default() {
        let opts = StreamOptions::default();
        assert!(opts.exclude.is_empty());
        assert!(opts.since_id.is_none());
        assert!(opts.max_retries.is_none());
    }

    #[test]
    fn test_stream_options_exclude_deltas() {
        let opts = StreamOptions::exclude_deltas();
        assert!(opts.exclude.contains(&"output.message.delta".to_string()));
        assert!(opts.exclude.contains(&"reason.thinking.delta".to_string()));
    }

    #[test]
    fn test_stream_options_builder() {
        let opts = StreamOptions::default()
            .with_since_id("event_123")
            .with_max_retries(5);
        assert_eq!(opts.since_id, Some("event_123".to_string()));
        assert_eq!(opts.max_retries, Some(5));
    }

    #[test]
    fn test_disconnecting_data_parse() {
        let json = r#"{"reason":"connection_cycle","retry_ms":100}"#;
        let data: DisconnectingData = serde_json::from_str(json).unwrap();
        assert_eq!(data.reason, "connection_cycle");
        assert_eq!(data.retry_ms, 100);
    }
}
