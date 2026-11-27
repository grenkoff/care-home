//! Demo source that plays the committed test pattern in a loop.

use std::sync::Arc;
use std::time::Duration;

use tokio::time::MissedTickBehavior;

use crate::domain::frames::{Frame, Framed, Pictures};
use crate::domain::mp4::TIMESCALE;
use crate::domain::nal::{AnnexB, Units};
use crate::domain::streams::{Recorded, Unrecorded};

/// Test pattern without people: H.264 in the Annex B format.
const PATTERN: &[u8] = include_bytes!("../../demo/pattern.h264");

/// Pictures a second of the test pattern.
pub const PATTERN_RATE: u32 = 15;

/// The committed test pattern as pictures.
#[derive(Debug, Clone, Copy, Default)]
pub struct Pattern;

impl Framed for Pattern {
    fn frames(&self) -> Vec<Frame> {
        Pictures::new(AnnexB::new(PATTERN).units()).frames()
    }
}

/// Source that keeps putting pictures into a stream.
pub trait Playing {
    /// Plays the pictures until one does not go into the stream, and returns why.
    fn play(&self) -> impl Future<Output = Result<(), Unrecorded>> + Send;
}

/// Demo that plays pictures in a loop into one stream at their rate.
#[derive(Debug)]
pub struct Demo<R> {
    /// Key of the stream.
    stream: String,
    /// Pictures of the loop.
    frames: Arc<[Frame]>,
    /// Pictures a second.
    rate: u32,
    /// Streams that take the pictures.
    streams: Arc<R>,
}

impl<R> Demo<R> {
    /// Creates the demo that plays the pictures at the rate into the stream.
    #[must_use]
    pub fn new(
        stream: impl Into<String>,
        frames: Arc<[Frame]>,
        rate: u32,
        streams: Arc<R>,
    ) -> Self {
        Self {
            stream: stream.into(),
            frames,
            rate,
            streams,
        }
    }
}

impl<R: Recorded + Send + Sync> Playing for Demo<R> {
    async fn play(&self) -> Result<(), Unrecorded> {
        let mut ticks = tokio::time::interval(Duration::from_secs(1) / self.rate);
        ticks.set_missed_tick_behavior(MissedTickBehavior::Delay);
        for frame in self.frames.iter().cycle() {
            ticks.tick().await;
            self.streams
                .record(&self.stream, frame, TIMESCALE / self.rate)?;
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use std::collections::BTreeMap;
    use std::sync::Arc;
    use std::time::Duration;

    use tokio::sync::mpsc::{UnboundedSender, unbounded_channel};
    use tokio::time::Instant;

    use super::{Demo, PATTERN_RATE, Pattern, Playing};
    use crate::domain::frames::{Frame, Framed, Picture};
    use crate::domain::mp4::Track;
    use crate::domain::nal::Unit;
    use crate::domain::sps::Size;
    use crate::domain::streams::{Recorded, Streams, Unrecorded};

    struct Tape {
        sender: UnboundedSender<(String, Frame, u32, Instant)>,
    }

    impl Recorded for Tape {
        fn record(&self, stream: &str, frame: &Frame, duration: u32) -> Result<(), Unrecorded> {
            self.sender
                .send((stream.to_owned(), frame.clone(), duration, Instant::now()))
                .map_err(|_| Unrecorded::Unknown(stream.to_owned()))
        }
    }

    fn frame(byte: u8) -> Frame {
        Frame::new(vec![Unit::new(vec![0x41, 0x9A, byte])])
    }

    #[tokio::test(start_paused = true)]
    async fn plays_the_pictures_in_a_loop_at_their_rate() {
        let (sender, mut receiver) = unbounded_channel();
        let frames: Arc<[Frame]> = Arc::from([frame(1), frame(2), frame(3)]);
        let demo = Demo::new("hall", frames, 15, Arc::new(Tape { sender }));
        let playing = tokio::spawn(async move { demo.play().await });
        let mut taken = Vec::new();
        while taken.len() < 7
            && let Some(record) = receiver.recv().await
        {
            taken.push(record);
        }
        playing.abort();
        assert_eq!(
            (
                taken
                    .iter()
                    .map(|(stream, frame, duration, _)| (stream.clone(), frame.clone(), *duration))
                    .collect::<Vec<_>>(),
                taken
                    .last()
                    .zip(taken.first())
                    .map(|(last, first)| last.3 - first.3)
            ),
            (
                [1, 2, 3, 1, 2, 3, 1]
                    .map(|byte| (String::from("hall"), frame(byte), 6000))
                    .to_vec(),
                Some(Duration::from_millis(400))
            )
        );
    }

    #[tokio::test(start_paused = true)]
    async fn keeps_its_rate_after_a_stall_instead_of_catching_up() {
        let (sender, mut receiver) = unbounded_channel();
        let demo = Demo::new("hall", Arc::from([frame(1)]), 15, Arc::new(Tape { sender }));
        let playing = tokio::spawn(async move { demo.play().await });
        let first = receiver.recv().await.map(|record| record.3);
        tokio::time::advance(Duration::from_secs(1)).await;
        let mut after = Vec::new();
        while after.len() < 3
            && let Some(record) = receiver.recv().await
        {
            after.push(record.3);
        }
        playing.abort();
        assert_eq!(
            (
                first.is_some(),
                after
                    .windows(2)
                    .map(|pair| pair[1] - pair[0] >= Duration::from_secs(1) / 15)
                    .collect::<Vec<_>>()
            ),
            (true, vec![true; 2])
        );
    }

    #[tokio::test(start_paused = true)]
    async fn stops_when_a_picture_does_not_go_into_the_stream() {
        let demo = Demo::new(
            "hall",
            Arc::from([frame(1)]),
            15,
            Arc::new(Streams::new(BTreeMap::new())),
        );
        assert_eq!(
            demo.play().await,
            Err(Unrecorded::Unknown(String::from("hall")))
        );
    }

    #[tokio::test(start_paused = true)]
    async fn plays_nothing_without_pictures() {
        let demo = Demo::new(
            "hall",
            Arc::from(Vec::new()),
            15,
            Arc::new(Streams::new(BTreeMap::new())),
        );
        assert_eq!(demo.play().await, Ok(()));
    }

    #[test]
    fn the_pattern_is_four_seconds_that_open_with_a_key_frame_and_its_track() {
        let frames = Pattern.frames();
        let track = Track::new(
            Size::new(640, 360),
            vec![
                0x67, 0x42, 0xC0, 0x1E, 0xD9, 0x00, 0xA0, 0x2F, 0xF9, 0x70, 0x11, 0x00, 0x00, 0x03,
                0x00, 0x01, 0x00, 0x00, 0x03, 0x00, 0x1E, 0x0F, 0x16, 0x2E, 0x48,
            ],
            vec![0x68, 0xCB, 0x81, 0x12, 0xC8],
        );
        assert_eq!(
            (
                frames.len() / usize::try_from(PATTERN_RATE).unwrap(),
                frames.first().map(Picture::key),
                frames.first().map(Picture::track),
            ),
            (4, Some(true), Some(Ok(Some(track))))
        );
    }
}
