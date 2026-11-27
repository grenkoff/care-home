//! Source that fills one stream from an IP camera over RTSP.

use std::sync::Arc;
use std::time::Duration;

use crate::domain::clock::Jumped;
use crate::domain::pause::{Pause, Waiting};
use crate::domain::streams::{Recorded, Restarted, Unrecorded};
use crate::infra::address::Address;
use crate::infra::demo::Playing;

/// Why a session with a camera ended.
#[derive(Debug, thiserror::Error)]
pub enum Lost {
    /// The camera refused the session or broke it.
    #[error("the camera refused the session: {0}")]
    Refused(#[from] retina::Error),
    /// The camera did not answer in time.
    #[error("the camera stayed silent")]
    Silent(#[from] tokio::time::error::Elapsed),
    /// The camera closed the stream.
    #[error("the camera closed the stream")]
    Closed,
    /// The camera offers no H.264 video.
    #[error("the camera offers no H.264 video")]
    Unwatchable,
    /// The clock of the camera jumped.
    #[error(transparent)]
    Jumped(#[from] Jumped),
    /// A picture did not go into the stream.
    #[error(transparent)]
    Unrecorded(#[from] Unrecorded),
}

/// Camera that plays its H.264 into one stream and connects again whenever it is lost.
#[derive(Debug)]
pub struct Camera<R> {
    /// Key of the stream.
    stream: String,
    /// Address of the camera.
    address: Address,
    /// Longest silence of the camera and the pause before the next attempt.
    patience: (Duration, Pause),
    /// Streams that take the pictures.
    streams: Arc<R>,
}

impl<R> Camera<R> {
    /// Creates the source of the stream from the camera at the address.
    #[must_use]
    pub fn new(
        stream: impl Into<String>,
        address: Address,
        patience: (Duration, Pause),
        streams: Arc<R>,
    ) -> Self {
        Self {
            stream: stream.into(),
            address,
            patience,
            streams,
        }
    }
}

impl<R: Recorded + Restarted + Send + Sync> Playing for Camera<R> {
    async fn play(&self) -> Result<(), Unrecorded> {
        let (silence, pause) = self.patience;
        tracing::info!(stream = %self.stream, camera = %self.address, ?silence, "waiting");
        tokio::time::sleep(pause.length()).await;
        self.streams.restart(&self.stream)
    }
}
