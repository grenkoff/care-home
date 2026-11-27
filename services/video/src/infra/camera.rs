//! Source that fills one stream from an IP camera over RTSP.

use std::convert::Infallible;
use std::future::poll_fn;
use std::sync::Arc;
use std::time::Duration;

use futures_core::Stream;
use retina::client::{
    Demuxed, PlayOptions, Session, SessionOptions, SetupOptions, TcpTransportOptions, Transport,
};
use retina::codec::{CodecItem, FrameFormat};
use tokio::time::timeout;

use crate::domain::clock::{Held, Jumped, Timed};
use crate::domain::frames::Frame;
use crate::domain::nal::{AnnexB, Units};
use crate::domain::pause::{Pause, Waiting};
use crate::domain::streams::{Recorded, Restarted, Unrecorded};
use crate::infra::address::{Address, Reached};
use crate::infra::demo::Playing;

/// Name the service gives itself to the cameras.
const AGENT: &str = "care-home-video";

/// Media of the stream the service watches.
const VIDEO: &str = "video";

/// Encoding of the stream the service watches.
const H264: &str = "h264";

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

impl<R: Recorded + Send + Sync> Camera<R> {
    /// Opens a session with the camera that plays its H.264 video over TCP.
    async fn session(&self) -> Result<Demuxed, Lost> {
        let (silence, _) = self.patience;
        let options = SessionOptions::default()
            .creds(self.address.credentials())
            .user_agent(AGENT.to_owned());
        let mut session =
            timeout(silence, Session::describe(self.address.location(), options)).await??;
        let video = session
            .streams()
            .iter()
            .position(|stream| stream.media() == VIDEO && stream.encoding_name() == H264)
            .ok_or(Lost::Unwatchable)?;
        let setup = SetupOptions::default()
            .transport(Transport::Tcp(TcpTransportOptions::default()))
            .frame_format(FrameFormat::SIMPLE);
        timeout(silence, session.setup(video, setup)).await??;
        let playing = timeout(silence, session.play(PlayOptions::default())).await??;
        Ok(playing.demuxed()?)
    }

    /// Puts the pictures of one session into the stream until the session ends, and says why.
    async fn relay(&self, delivered: &mut bool) -> Result<Infallible, Lost> {
        let (silence, _) = self.patience;
        let mut session = Box::pin(self.session().await?);
        let mut held = Held::new();
        loop {
            let item = timeout(
                silence,
                poll_fn(|context| session.as_mut().poll_next(context)),
            )
            .await?
            .ok_or(Lost::Closed)??;
            if let CodecItem::VideoFrame(frame) = item {
                let picture = Frame::new(AnnexB::new(frame.data()).units());
                let (next, released) = held.followed(frame.timestamp().elapsed(), picture)?;
                held = next;
                if let Some((picture, duration)) = released {
                    self.streams.record(&self.stream, &picture, duration)?;
                    *delivered = true;
                }
            }
        }
    }
}

impl<R: Recorded + Restarted + Send + Sync> Playing for Camera<R> {
    async fn play(&self) -> Result<(), Unrecorded> {
        let (_, mut pause) = self.patience;
        loop {
            let mut delivered = false;
            let Err(lost) = self.relay(&mut delivered).await;
            if let Lost::Unrecorded(Unrecorded::Unknown(stream)) = lost {
                return Err(Unrecorded::Unknown(stream));
            }
            tracing::warn!(stream = %self.stream, camera = %self.address, %lost, "camera lost");
            if delivered {
                self.streams.restart(&self.stream)?;
                pause = pause.shortest();
            }
            tokio::time::sleep(pause.length()).await;
            pause = pause.longer();
        }
    }
}
