//! Source that fills one stream from an IP camera over RTSP.

use std::future::poll_fn;
use std::pin::Pin;
use std::sync::Arc;
use std::time::Duration;

use futures_core::Stream;
use retina::client::{
    Demuxed, PlayOptions, Session, SessionOptions, SetupOptions, TcpTransportOptions, Transport,
};
use retina::codec::{CodecItem, FrameFormat};
use tokio::time::{Instant, timeout, timeout_at};

use crate::domain::clock::{Held, Jumped, Timed};
use crate::domain::frames::Frame;
use crate::domain::nal::{AnnexB, Units};
use crate::domain::pause::{Pause, Waiting};
use crate::domain::streams::{Recorded, Restarted, Unrecorded};
use crate::infra::address::{Address, Reached};
use crate::infra::sources::Playing;

/// Name the service gives itself to the cameras.
const AGENT: &str = "care-home-video";

/// Media of the stream the service watches.
const VIDEO: &str = "video";

/// Encoding of the stream the service watches.
const H264: &str = "h264";

/// Why a session with a camera ended.
#[derive(Debug, thiserror::Error)]
pub enum Lost {
    /// The camera refused the session, or the session broke.
    #[error("the session with the camera failed: {0}")]
    Failed(#[from] retina::Error),
    /// The camera did not answer or sent no picture in time.
    #[error("the camera stayed silent")]
    Silent(#[from] tokio::time::error::Elapsed),
    /// The camera closed the stream.
    #[error("the camera closed the stream")]
    Closed,
    /// The camera offers no H.264 video.
    #[error("the camera offers no H.264 video")]
    Unwatchable,
    /// The clock of the camera went back or jumped too far.
    #[error(transparent)]
    Jumped(#[from] Jumped),
    /// A picture did not go into the stream.
    #[error(transparent)]
    Unrecorded(#[from] Unrecorded),
}

/// How one session with a camera ended.
#[derive(Debug)]
struct Ended {
    /// Why the session ended.
    lost: Lost,
    /// Whether a picture of the session went into the stream.
    delivered: bool,
}

/// Adapter: plays the H.264 of an IP camera into one stream and connects again when it is lost.
#[derive(Debug)]
pub struct Camera<R> {
    /// Key of the stream.
    stream: String,
    /// Address of the camera.
    address: Address,
    /// Longest the camera may stay silent.
    silence: Duration,
    /// Pause before the next attempt to reach the camera.
    pause: Pause,
    /// Streams that take the pictures.
    streams: Arc<R>,
}

impl<R> Camera<R> {
    /// Creates the source of the stream from the camera, given its silence and pause.
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
            silence: patience.0,
            pause: patience.1,
            streams,
        }
    }
}

impl<R: Recorded + Send + Sync> Camera<R> {
    /// Opens a session with the camera that plays its H.264 video over TCP.
    async fn session(&self) -> Result<Demuxed, Lost> {
        let options = SessionOptions::default()
            .creds(self.address.credentials())
            .user_agent(AGENT.to_owned());
        let mut session = timeout(
            self.silence,
            Session::describe(self.address.location(), options),
        )
        .await??;
        let video = session
            .streams()
            .iter()
            .position(|stream| stream.media() == VIDEO && stream.encoding_name() == H264)
            .ok_or(Lost::Unwatchable)?;
        let setup = SetupOptions::default()
            .transport(Transport::Tcp(TcpTransportOptions::default()))
            .frame_format(FrameFormat::SIMPLE);
        timeout(self.silence, session.setup(video, setup)).await??;
        let playing = timeout(self.silence, session.play(PlayOptions::default())).await??;
        Ok(playing.demuxed()?)
    }

    /// Takes the next picture of the session with its time, unless the camera falls silent first.
    async fn picture(&self, session: &mut Pin<Box<Demuxed>>) -> Result<(i64, Frame), Lost> {
        let deadline = Instant::now() + self.silence;
        loop {
            let item = timeout_at(
                deadline,
                poll_fn(|context| session.as_mut().poll_next(context)),
            )
            .await?
            .ok_or(Lost::Closed)??;
            if let CodecItem::VideoFrame(frame) = item {
                let picture = Frame::new(AnnexB::new(frame.data()).units());
                return Ok((frame.timestamp().elapsed(), picture));
            }
        }
    }

    /// Records the picture the clock held once the next one came, and tells whether it did.
    async fn recorded(
        &self,
        session: &mut Pin<Box<Demuxed>>,
        held: Held,
    ) -> Result<(Held, bool), Lost> {
        let (time, picture) = self.picture(session).await?;
        let (held, released) = held.followed(time, picture)?;
        if let Some((picture, duration)) = &released {
            self.streams.record(&self.stream, picture, *duration)?;
        }
        Ok((held, released.is_some()))
    }

    /// Puts the pictures of one session into the stream and tells how the session ended.
    async fn relay(&self) -> Ended {
        let mut session = match self.session().await {
            Ok(session) => Box::pin(session),
            Err(lost) => {
                return Ended {
                    lost,
                    delivered: false,
                };
            }
        };
        let mut held = Held::new();
        let mut delivered = false;
        loop {
            match self.recorded(&mut session, held).await {
                Ok((next, recorded)) => {
                    held = next;
                    delivered |= recorded;
                }
                Err(lost) => return Ended { lost, delivered },
            }
        }
    }
}

impl<R: Recorded + Restarted + Send + Sync> Playing for Camera<R> {
    async fn play(&self) -> Result<(), Unrecorded> {
        let mut pause = self.pause;
        loop {
            let Ended { lost, delivered } = self.relay().await;
            if let Lost::Unrecorded(Unrecorded::Unknown(stream)) = &lost {
                return Err(Unrecorded::Unknown(stream.clone()));
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
