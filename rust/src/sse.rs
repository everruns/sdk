//! Server-Sent Events (SSE) streaming

use crate::client::Everruns;
use crate::error::{Error, Result};
use crate::models::Event;
use futures::stream::Stream;
use std::pin::Pin;
use std::task::{Context, Poll};

/// Options for SSE streaming
#[derive(Debug, Clone, Default)]
pub struct StreamOptions {
    /// Event types to exclude from the stream
    pub exclude: Vec<String>,
    /// Resume from a specific event ID
    pub since_id: Option<String>,
}

impl StreamOptions {
    /// Create options that exclude delta events (for reduced bandwidth)
    pub fn exclude_deltas() -> Self {
        Self {
            exclude: vec![
                "output.message.delta".to_string(),
                "reason.thinking.delta".to_string(),
            ],
            since_id: None,
        }
    }
}

/// A stream of SSE events from a session
pub struct EventStream {
    client: Everruns,
    session_id: String,
    options: StreamOptions,
    inner: Option<Pin<Box<dyn Stream<Item = Result<Event>> + Send>>>,
    last_event_id: Option<String>,
}

impl EventStream {
    pub(crate) fn new(client: Everruns, session_id: String, options: StreamOptions) -> Self {
        Self {
            client,
            session_id,
            options,
            inner: None,
            last_event_id: None,
        }
    }

    /// Get the last received event ID (for resuming)
    pub fn last_event_id(&self) -> Option<&str> {
        self.last_event_id.as_deref()
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

            let exclude_refs: Vec<&str> = exclude.iter().map(|s| s.as_str()).collect();
            let url = client.sse_url(&session_id, since_id.as_deref(), &exclude_refs);

            let request = reqwest::Client::new()
                .get(url)
                .header("Authorization", client.auth_header())
                .header("Accept", "text/event-stream");

            let mut es = EventSource::new(request).map_err(|e| Error::Sse(e.to_string()))?;

            use futures::StreamExt;
            while let Some(event) = es.next().await {
                match event {
                    Ok(SseEvent::Open) => {
                        tracing::debug!("SSE connection opened");
                    }
                    Ok(SseEvent::Message(msg)) => {
                        if let Ok(event) = serde_json::from_str::<Event>(&msg.data) {
                            yield event;
                        }
                    }
                    Err(e) => {
                        tracing::warn!("SSE error: {}", e);
                        // Could implement reconnection logic here
                        return Err(Error::Sse(e.to_string()));
                    }
                }
            }
        })
    }
}

impl Stream for EventStream {
    type Item = Result<Event>;

    fn poll_next(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Option<Self::Item>> {
        if self.inner.is_none() {
            self.inner = Some(self.connect());
        }

        let inner = self.inner.as_mut().unwrap();
        match Pin::new(inner).poll_next(cx) {
            Poll::Ready(Some(Ok(event))) => {
                self.last_event_id = Some(event.id.clone());
                Poll::Ready(Some(Ok(event)))
            }
            Poll::Ready(Some(Err(e))) => Poll::Ready(Some(Err(e))),
            Poll::Ready(None) => Poll::Ready(None),
            Poll::Pending => Poll::Pending,
        }
    }
}
